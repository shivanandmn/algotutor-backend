import os
import time
import requests
from datetime import datetime
from typing import Dict, Any, List, Optional
from beanie import PydanticObjectId
from fastapi import HTTPException

from app.core.config import settings
from app.models.code_submission import CodeSubmission, TestResult

class CodeExecutionService:
    def __init__(self):
        self.judge0_api_url = "https://judge0-ce.p.rapidapi.com"
        self.headers = {
            "x-rapidapi-key": settings.JUDGE0_API_KEY,
            "x-rapidapi-host": "judge0-ce.p.rapidapi.com",
            "content-type": "application/json"
        }
        self.language_configs = {
            "python": {
                "judge0_id": 71,  # Python (3.8.1)
                "extension": ".py",
                "timeout": 10,  # seconds
            },
            "java": {
                "judge0_id": 62,  # Java (OpenJDK 13.0.1)
                "extension": ".java",
                "timeout": 15,
            },
            "cpp": {
                "judge0_id": 54,  # C++ (GCC 9.2.0)
                "extension": ".cpp",
                "timeout": 10,
            },
            "javascript": {
                "image": "node:16-slim",
                "extension": ".js",
                "command": "node",
                "memory_limit": "256m",
                "timeout": 10,
                "compile_needed": False
            }
        }

    async def execute_code(self, code: str, lang: str, input_data: str) -> Dict[str, Any]:
        """Execute code using Judge0 CE API and return result"""
        try:
            config = self.language_configs[lang]

            # Prepare submission data
            submission_data = {
                "source_code": code,
                "language_id": config['judge0_id'],
                "stdin": input_data,
                "cpu_time_limit": config['timeout'],
                "memory_limit": 256000  # 256MB in KB
            }

            # Create submission
            response = requests.post(
                f"{self.judge0_api_url}/submissions",
                headers=self.headers,
                json=submission_data
            )
            response.raise_for_status()
            token = response.json()['token']

            # Poll for results
            max_attempts = 10
            attempt = 0
            while attempt < max_attempts:
                response = requests.get(
                    f"{self.judge0_api_url}/submissions/{token}",
                    headers=self.headers
                )
                response.raise_for_status()
                result = response.json()

                if result['status']['id'] not in [1, 2]:  # Not queued or processing
                    break

                attempt += 1
                time.sleep(1)

            # Process results
            status = result['status']['id']
            if status == 3:  # Accepted
                return {
                    "status": "success",
                    "output": result.get('stdout', ''),
                    "error": None
                }
            elif status == 5:  # Time Limit Exceeded
                return {
                    "status": "error",
                    "output": "",
                    "error": f"Code execution timed out after {config['timeout']} seconds"
                }
            else:
                return {
                    "status": "error",
                    "output": result.get('stdout', ''),
                    "error": result.get('stderr', '') or result.get('compile_output', '')
                }

        except Exception as e:
            return {
                "status": "error",
                "output": "",
                "error": str(e)
            }

    async def queue_submission(
        self,
        user_id: str,
        question_id: str,
        language: str,
        code: str
    ) -> str:
        """Queue a code submission for execution"""
        if language not in self.language_configs:
            raise HTTPException(
                status_code=400,
                detail=f"Language {language} not supported"
            )

        # Create submission record
        submission = CodeSubmission(
            user=PydanticObjectId(user_id),
            question=PydanticObjectId(question_id),
            language=language,
            code=code,
            status="pending"
        )
        await submission.insert()
        
        return str(submission.id)

    async def execute_submission(self, submission_id: str):
        """Execute a queued code submission"""
        submission = await CodeSubmission.get(PydanticObjectId(submission_id))
        if not submission:
            raise HTTPException(status_code=404, detail="Submission not found")

        question = await Question.get(submission.question.id)
        if not question:
            raise HTTPException(status_code=404, detail="Question not found")

        # Update status to running
        submission.status = "running"
        await submission.save()

        try:
            # Create temporary directory for code files
            with tempfile.TemporaryDirectory() as temp_dir:
                results = await self._run_test_cases(
                    submission.language,
                    submission.code,
                    question.test_cases,
                    temp_dir
                )

                # Update submission with results
                submission.results = results
                submission.total_tests = len(results)
                submission.total_passed = sum(1 for r in results if r.passed)
                submission.status = "completed"
                submission.completed_at = datetime.utcnow()
                
                # Calculate total execution time and peak memory
                submission.execution_time = sum(r.execution_time for r in results)
                submission.memory_used = max(r.memory_used for r in results)
                
                await submission.save()

        except Exception as e:
            submission.status = "error"
            submission.completed_at = datetime.utcnow()
            await submission.save()
            raise HTTPException(status_code=500, detail=str(e))

    async def _run_test_cases(
        self,
        language: str,
        code: str,
        test_cases: List[dict],
        temp_dir: str
    ) -> List[TestResult]:
        """Run test cases with compilation support for compiled languages"""
        config = self.language_configs[language]
        results = []

        # Create source file
        source_file = os.path.join(temp_dir, f"main{config['extension']}")
        with open(source_file, "w") as f:
            f.write(code)

        # Compile if needed
        if config.get('compile_needed', False):
            try:
                compile_cmd = [config['compile_command'], f"main{config['extension']}"] + config.get('compile_args', [])
                container = self.client.containers.create(
                    image=config['image'],
                    command=compile_cmd,
                    volumes={temp_dir: {'bind': '/code', 'mode': 'rw'}},
                    working_dir='/code',
                    network_disabled=True
                )
                container.start()
                result = container.wait(timeout=30)  # 30 seconds compile timeout
                
                if result['StatusCode'] != 0:
                    compile_error = container.logs(stderr=True).decode()
                    container.remove(force=True)
                    return [TestResult(
                        test_case_id='compile',
                        passed=False,
                        execution_time=0,
                        memory_used=0,
                        error=f"Compilation error:\n{compile_error}"
                    )]
                container.remove(force=True)
            except Exception as e:
                return [TestResult(
                    test_case_id='compile',
                    passed=False,
                    execution_time=0,
                    memory_used=0,
                    error=f"Compilation failed: {str(e)}"
                )]

        """Run code against test cases in Docker container"""
        config = self.language_configs[language]
        results = []

        # Create source file
        source_file = os.path.join(temp_dir, f"main{config['extension']}")
        with open(source_file, "w") as f:
            f.write(code)

        for test_case in test_cases:
            try:
                # Create container
                container = self.client.containers.create(
                    image=config["image"],
                    command=self._get_run_command(language, "main", test_case["input"]),
                    volumes={
                        temp_dir: {
                            "bind": "/code",
                            "mode": "rw"
                        }
                    },
                    working_dir="/code",
                    mem_limit=config["memory_limit"],
                    network_disabled=True,
                    cpu_period=100000,
                    cpu_quota=25000  # 25% CPU limit
                )

                start_time = datetime.now()
                container.start()

                try:
                    container.wait(timeout=config["timeout"])
                    execution_time = (datetime.now() - start_time).total_seconds() * 1000
                    
                    # Get output and memory usage
                    output = container.logs().decode().strip()
                    stats = container.stats(stream=False)
                    memory_used = stats["memory_stats"]["usage"] / (1024 * 1024)  # Convert to MB

                    # Compare with expected output
                    passed = output.strip() == test_case["expected_output"].strip()

                    results.append(TestResult(
                        test_case_id=str(test_case["id"]),
                        passed=passed,
                        execution_time=execution_time,
                        memory_used=memory_used,
                        output=output if not test_case["is_hidden"] else None,
                        is_hidden=test_case["is_hidden"]
                    ))

                except Exception as e:
                    results.append(TestResult(
                        test_case_id=str(test_case["id"]),
                        passed=False,
                        execution_time=0,
                        memory_used=0,
                        error=str(e),
                        is_hidden=test_case["is_hidden"]
                    ))

                finally:
                    try:
                        container.remove(force=True)
                    except:
                        pass

            except Exception as e:
                results.append(TestResult(
                    test_case_id=str(test_case["id"]),
                    passed=False,
                    execution_time=0,
                    memory_used=0,
                    error=f"Container error: {str(e)}",
                    is_hidden=test_case["is_hidden"]
                ))

        return results

    def _get_run_command(self, language: str, filename: str, input_data: str) -> List[str]:
        """Get the appropriate run command for the language"""
        if language == "python":
            return ["python", f"{filename}.py"]
        elif language == "java":
            return ["java", filename]
        elif language == "cpp":
            return [f"./{filename}"]
        else:
            raise ValueError(f"Unsupported language: {language}")

    async def get_submission_status(self, submission_id: str) -> Optional[CodeSubmission]:
        """Get the status of a submission"""
        return await CodeSubmission.get(PydanticObjectId(submission_id))

    async def get_user_submissions(
        self,
        user_id: str,
        question_id: Optional[str] = None,
        limit: int = 10
    ) -> List[CodeSubmission]:
        """Get submissions for a user"""
        query = {"user": PydanticObjectId(user_id)}
        if question_id:
            query["question"] = PydanticObjectId(question_id)
        
        return await CodeSubmission.find(query).limit(limit).to_list()
