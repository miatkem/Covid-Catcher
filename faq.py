"""API Call for FAQ's"""
import requests

def get_all_questions():
    """API call for FAQ"""
    questions = []
    url = ("https://faq.coronavirus.gov/api/v2/questions.json")
    response=requests.get(url)
    data = response.json()
    max_num_faqs = 0
    for question in data:
        q=question['title']
        if q != 'None':
            a=question['answer']
            a_html=question['answer_html']
            sources = ''
            for source in question['sources']:
                sources+=source['agency'] + ', '
            sources = sources[:-2]
            questions.append(FAQ(q,a,a_html,sources))
            max_num_faqs += 1
            if max_num_faqs == 25:
                break
    return questions

class FAQ:
    """FAQ Class"""
    def __init__(self, question, answer, answer_html, source):
        self.question = question
        self.answer = answer
        self.answer_html = answer_html
        self.source = source
        