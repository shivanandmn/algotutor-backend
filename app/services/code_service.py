import os
import docker
import tempfile
from datetime import datetime
from typing import Dict, Any, List, Optional
from beanie import PydanticObjectId
from fastapi import HTTPException

from app.core.config import settings
from app.models.code_submission import CodeSubmission, TestResult

class CodeExecutionService:
    def __init__(self):
        self.client = docker.DockerClient(base_url='unix:///var/run/docker.sock')
        self.language_configs = {
            "python": {
                "image": "python:3.9-slim",
                "extension": ".py",
                "command": "python",
                "memory_limit": "256m",
                "timeout": 10,  # seconds
                "compile_needed": False
            },
            "java": {
                "image": "openjdk:11-slim",
                "extension": ".java",
                "command": "java",
                "compile_command": "javac",
                "memory_limit": "512m",
                "timeout": 15,
                "compile_needed": True
            },
            "cpp": {
                "image": "gcc:latest",
                "extension": ".cpp",
                "command": "./main",
                "compile_command": "g++",
                "compile_args": ["-o", "main"],
                "memory_limit": "256m",
                "timeout": 10,
                "compile_needed": True
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
        """Execute code and return result"""
        try:
            config = self.language_configs[lang]
            file_name = f"main{config['extension']}"

            # Create a temporary directory for code execution
            with tempfile.TemporaryDirectory() as temp_dir:
                # Write code and input files safely
                code_path = os.path.join(temp_dir, file_name)
                input_path = os.path.join(temp_dir, 'input.txt')
                
                with open(code_path, 'w') as f:
                    f.write(code)
                with open(input_path, 'w') as f:
                    f.write(input_data)

                # Create container with proper volume mounting
                container = self.client.containers.run(
                    image=config["image"],
                    command=[config["command"], file_name],
                    volumes={
                        temp_dir: {"bind": "/code", "mode": "ro"}
                    },
                    working_dir="/code",
                    detach=True,
                    mem_limit=config["memory_limit"],
                    network_disabled=True,
                    cpu_period=100000,
                    cpu_quota=25000,  # 25% CPU limit
                    security_opt=['no-new-privileges'],
                    read_only=True
                )

                try:
                    # Run code with timeout
                    result = container.wait(timeout=config["timeout"])
                    output = container.logs().decode("utf-8")

                    return {
                        "status": "success" if result["StatusCode"] == 0 else "error",
                        "output": output,
                        "error": None if result["StatusCode"] == 0 else output
                    }
                finally:
                    # Ensure container cleanup
                    try:
                        container.remove(force=True)
                    except Exception:
                        pass

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
