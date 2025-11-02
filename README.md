# knowmona

Knowmona is an AI-powred larning game that allows anyone to create quizzes about anything just by typing any topic!

<video width="630" height="300" src="https://github.com/user-attachments/assets/b97d5c75-f9f3-42ed-9740-23cc4a864cdf
"></video>

It is a application gives out a multiple choices and explanations for the questions in th quiz and a list of sources refered to by the LLM. A user can also uload files, such as PDFs and DOCXs, and the AI will generate a quiz about it. There is also are feature wherein users can friend other users and publicly share the quizzies that they have created with them. The difficulty and the tine of the quiz can also be  personalized by the user.

It uses Django as its web framework, Open AI's LLMs for content genration, Google's programmable search engine for extracting external information used for reference and Heroku of web hosting.

## Prequisities

-  AWS S3 Bucket for multimedia data storage
-  Open AI API access
-  Google OAuth for alternative user login
-  Programmable Google Search Engline access
-  Heroku for cloud web server

## Instalation
Create a virtual environment for the repository:
```powershell
python -m venv venv
```

Run the virtual environment:
```powershell
venv/Scripts/Activate.ps1
```

Install the required libraries and tools:
```powershell
pip install -r requirements.txt
```

Create an .env file and input API keys for access to third party services:
```env
AWS_ACCESS_KEY_ID=<<AWS_ACCESS_KEY_ID>>
AWS_SECRET_ACCESS_KEY=<<AWS_SECRET_ACCESS_KEY>>
AWS_S3_REGION_NAME=<<AWS_S3_REGION_NAME>>
AWS_STORAGE_BUCKET_NAME=<<AWS_STORAGE_BUCKET_NAME>>

# AI inference serivce
OPENAI_API_KEY=<<OPENAI_API_KEY>>

# Google authenication and web services
GOOGLE_OAUTH_CLIENT_ID=<<GOOGLE_OAUTH_CLIENT_ID>>
GOOGLE_API_KEY=<<GOOGLE_API_KEY>>
SEARCH_ENGINE_ID=<<SEARCH_ENGINE_ID>>

# Google email SMTP server
EMAIL_HOST_APP_PASSWORD=<<EMAIL_HOST_APP_PASSWORD>>
```

Create a Heroku account and run it locally:
```powershell
heroku local
```



