from pymongo import MongoClient
from dotenv import load_dotenv
import os
from datetime import datetime
from typing import List

# Load environment variables
load_dotenv()

# MongoDB connection
MONGODB_URL = os.getenv("MONGODB_URL")
DATABASE_NAME = os.getenv("DATABASE_NAME")

client = MongoClient(MONGODB_URL)
db = client[DATABASE_NAME]
questions_collection = db["questions"]

# Sample LeetCode questions
sample_questions = [
    {
        "title": "Two Sum",
        "difficulty": "Easy",
        "description": """Given an array of integers nums and an integer target, return indices of the two numbers in nums such that they add up to target.
You may assume that each input would have exactly one solution, and you may not use the same element twice.""",
        "examples": [
            {
                "input": "nums = [2,7,11,15], target = 9",
                "output": "[0,1]",
                "explanation": "Because nums[0] + nums[1] == 9, we return [0, 1]."
            }
        ],
        "constraints": [
            "2 <= nums.length <= 104",
            "-109 <= nums[i] <= 109",
            "-109 <= target <= 109",
            "Only one valid answer exists."
        ],
        "starter_code": {
            "python": """def two_sum(nums: List[int], target: int) -> List[int]:
    pass""",
            "javascript": """function twoSum(nums, target) {
    
}""",
            "java": """class Solution {
    public int[] twoSum(int[] nums, int target) {
        
    }
}"""
        },
        "test_cases": [
            {"input": {"nums": [2,7,11,15], "target": 9}, "output": [0,1]},
            {"input": {"nums": [3,2,4], "target": 6}, "output": [1,2]},
            {"input": {"nums": [3,3], "target": 6}, "output": [0,1]}
        ],
        "created_at": datetime.utcnow()
    },
    {
        "title": "Valid Parentheses",
        "difficulty": "Easy",
        "description": """Given a string s containing just the characters '(', ')', '{', '}', '[' and ']', determine if the input string is valid.
An input string is valid if:
1. Open brackets must be closed by the same type of brackets.
2. Open brackets must be closed in the correct order.""",
        "examples": [
            {
                "input": "s = \"()\"",
                "output": "true",
                "explanation": "The parentheses match and are in correct order."
            }
        ],
        "constraints": [
            "1 <= s.length <= 104",
            "s consists of parentheses only '()[]{}'."
        ],
        "starter_code": {
            "python": """def is_valid(s: str) -> bool:
    pass""",
            "javascript": """function isValid(s) {
    
}""",
            "java": """class Solution {
    public boolean isValid(String s) {
        
    }
}"""
        },
        "test_cases": [
            {"input": {"s": "()"}, "output": True},
            {"input": {"s": "()[]{}"}, "output": True},
            {"input": {"s": "(]"}, "output": False}
        ],
        "created_at": datetime.utcnow()
    }
]

def seed_questions():
    try:
        # Clear existing questions
        questions_collection.delete_many({})
        
        # Insert new questions
        result = questions_collection.insert_many(sample_questions)
        print(f"Successfully inserted {len(result.inserted_ids)} questions")
        
    except Exception as e:
        print(f"Error seeding questions: {str(e)}")
    finally:
        client.close()

if __name__ == "__main__":
    seed_questions()
