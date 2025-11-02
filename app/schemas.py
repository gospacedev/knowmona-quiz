from pydantic import BaseModel, Field

# The defined architecture of the quiz model


class QuizQuestionBlock(BaseModel):
    question: str
    choice_1: str
    choice_2: str
    choice_3: str
    choice_4: str
    answer: str
    explanation: str


class QuizSchematic(BaseModel):
    Q1: QuizQuestionBlock = Field(..., alias="Q1")
    Q2: QuizQuestionBlock = Field(..., alias="Q2")
    Q3: QuizQuestionBlock = Field(..., alias="Q3")
    Q4: QuizQuestionBlock = Field(..., alias="Q4")
    Q5: QuizQuestionBlock = Field(..., alias="Q5")
    Q6: QuizQuestionBlock = Field(..., alias="Q6")
    Q7: QuizQuestionBlock = Field(..., alias="Q7")
    Q8: QuizQuestionBlock = Field(..., alias="Q8")
    Q9: QuizQuestionBlock = Field(..., alias="Q9")
    Q10: QuizQuestionBlock = Field(..., alias="Q10")