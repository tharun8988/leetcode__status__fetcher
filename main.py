from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import pandas as pd
import requests
import io

app = FastAPI(title="LeetCode Stats API")

def fetch_stats(username: str):
    query = {
        "query": """
        query getUserProfile($username: String!) {
            matchedUser(username: $username) {
                submitStats {
                    acSubmissionNum {
                        difficulty
                        count
                    }
                }
            }
        }
        """,
        "variables": {"username": username}
    }
    try:
        res = requests.post("https://leetcode.com/graphql", json=query)
        if res.status_code != 200:
            return None
        data = res.json()
        user = data["data"]["matchedUser"]
        if not user:
            return None
        submissions = user["submitStats"]["acSubmissionNum"]
        return {entry["difficulty"]: entry["count"] for entry in submissions}
    except Exception as e:
        print("Error fetching stats for", username, e)
        return None

@app.post("/upload-excel/")
async def upload_excel(file: UploadFile = File(...)):
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Please upload an Excel file with .xlsx or .xls extension")

    contents = await file.read()

    try:
        df = pd.read_excel(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read Excel file: {str(e)}")

    url_col = 'Paste your Leetcode profile link'
    username_col = 'Leetcode username'

    if url_col in df.columns:
        column = url_col
        mode = "url"
    elif username_col in df.columns:
        column = username_col
        mode = "username"
    else:
        raise HTTPException(status_code=400,
                            detail=f"Excel must have a column named '{url_col}' or '{username_col}'")

    results = {}

    for val in df[column]:
        if not isinstance(val, str) or not val.strip():
            results[str(val)] = {"error": "Invalid or empty value"}
            continue

        if mode == "url":
            if "leetcode.com" not in val:
                results[val] = {"error": "Invalid LeetCode profile URL"}
                continue
            username = val.rstrip("/").split("/")[-1].strip()
        else:
            username = val.strip()

        stats = fetch_stats(username)
        if stats is None:
            results[username] = {"error": "Failed to fetch stats or user not found"}
        else:
            results[username] = stats

    return JSONResponse(content=results)
