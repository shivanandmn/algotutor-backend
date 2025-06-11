import time
import requests
from datetime import datetime
from typing import Dict, Any, List, Optional
from beanie import PydanticObjectId, Link
from fastapi import HTTPException
import tempfile
from app.core.config import settings
from app.models.code_submission import CodeSubmission, TestResult
from app.models.user import User
from app.models.question import Question, TestCase

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
            raise HTTPException(status_code=404, detail="Su-bmission not found")

        question = await Question.get(submission.question)
        if not question:
            raise HTTPException(status_code=404, detail="Question not found")

        # Update status to running
        submission.status = "running"
        await submission.save()

        try:
            results = await self._run_test_cases(
                language=submission.language,
                code=submission.code,
                test_cases=question.test_cases
            )

            # Update submission with results
            submission.status = "completed"
            submission.completed_at = datetime.utcnow()
            submission.results = results
            submission.total_tests = len(results)
            submission.total_passed = sum(1 for r in results if r.passed)
            
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
        test_cases: List[TestCase]
    ) -> List[TestResult]:
        """Run test cases using Judge0 API"""
        config = self.language_configs[language]
        results = []

        for test_case in test_cases:
            try:
                # Prepare submission data
                data = {
                    "source_code": code,
                    "language_id": config["judge0_id"],
                    "stdin": test_case.input,
                    "expected_output": test_case.expected_output,
                    "cpu_time_limit": 2,  # 2 seconds
                    "memory_limit": 256000  # 256MB
                }

                # Create submission
                response = requests.post(
                    f"{self.judge0_api_url}/submissions",
                    headers=self.headers,
                    json=data
                )
                response.raise_for_status()
                token = response.json()["token"]

                # Wait for result (poll every 0.5 seconds)
                while True:
                    response = requests.get(
                        f"{self.judge0_api_url}/submissions/{token}",
                        headers=self.headers
                    )
                    response.raise_for_status()
                    submission = response.json()

                    if submission["status"]["id"] not in [1, 2]:  # Not queued or processing
                        break
                    time.sleep(0.5)

                # Process result
                status = submission["status"]
                passed = status["id"] == 3  # Accepted
                error = None if passed else f"{status['description']}: {submission.get('compile_output', '')}"

                # Generate test case ID if not present
                test_case_id = getattr(test_case, 'id', None) or str(PydanticObjectId())
                results.append(TestResult(
                    test_case_id=str(test_case_id),
                    passed=passed,
                    execution_time=float(submission.get("time", 0)),
                    memory_used=float(submission.get("memory", 0)) / 1024,  # Convert KB to MB
                    output=None if test_case.is_hidden else submission.get("stdout", ""),
                    error=error,
                    is_hidden=test_case.is_hidden
                ))

            except Exception as e:
                test_case_id = getattr(test_case, 'id', None) or str(PydanticObjectId())
                results.append(TestResult(
                    test_case_id=str(test_case_id),
                    passed=False,
                    execution_time=0,
                    memory_used=0,
                    error=f"Judge0 API error: {str(e)}",
                    is_hidden=test_case.is_hidden
                ))

        return results

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

    async def get_question_submissions(
        self,
        question_id: str,
        limit: int = 50
    ) -> List[CodeSubmission]:
        """Get all submissions for a specific question"""
        query = {"question": PydanticObjectId(question_id)}
        return await CodeSubmission.find(query).limit(limit).to_list()
