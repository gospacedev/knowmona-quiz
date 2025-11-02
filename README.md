# knowmona

Knowmona is an AI-powred larning game that allows anyone to create quizzes about anything just by typing any topic!

It is a application gives out a multiple choices and explanations for the questions in th quiz and a list of sources refered to by the LLM. A user can also uload files, such as PDFs and DOCXs, and the AI will generate a quiz about it. There is also are feature wherein users can friend other users and publicly share the quizzies that they have created with them. The difficulty and the tine of the quiz can also be  personalized by the user.

It uses Django as its web framework, Open AI's LLMs for content genration, Google's programmable search engine for extracting external information used for reference and Heroku of web hosting.

## Prequisities

-  AWS S3 Bucket for multimedia data storage
-  Open AI API access
-  Google OAuth for alternative user login
-  Programmable Google Search Engline access
-  Heroku for cloud web server

## Instalation
Create a virtual environment:
```powershell
python -m venv exoseeker-venv
```



