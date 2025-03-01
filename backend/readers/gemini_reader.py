from google import genai


class GeminiPDFReader:
    def __init__(self, api_key):
        self.client = genai.Client(api_key=api_key)

    def ask_pdf(self, question, pdf_path, model="gemini-2.0-flash-exp"):
        file_ref = self.client.files.upload(file=pdf_path)
        try:
            response = self.client.models.generate_content(
                model=model,
                contents=[question, file_ref],
            )
            return response.text
        except Exception as e:
            print(f"An error occurred: {e}")
            return None

    def dump_response(self, response, out_path):
        # 一般是markdown格式
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(response)


if __name__ == "__main__":
    import os
    import glob
    from dotenv import load_dotenv

    load_dotenv()

    api_key = os.getenv("API_KEY")
    gemini = GeminiPDFReader(api_key)
    pdf_files = glob.glob("../data/papers/*.pdf")
    # 论文十问由沈向洋博士提出，他鼓励大家带着这十个问题去阅读论文，用有用的信息构建认知模型。
    question = """
    请你认真阅读论文，用中文回答以下问题：
    Q1. 论文试图解决什么问题？
    Q2. 这是否是一个新的问题？
    Q3. 这篇文章要验证一个什么科学假设？
    Q4. 有哪些相关研究？如何归类？谁是这一课题在领域内值得关注的研究员？
    Q5. 论文中提到的解决方案之关键是什么？
    Q6. 论文中的实验是如何设计的？
    Q7. 用于定量评估的数据集是什么？代码有没有开源？
    Q8. 论文中的实验及结果有没有很好地支持需要验证的科学假设？
    Q9. 这篇论文到底有什么贡献？
    Q10. 下一步呢？有什么工作可以继续深入？
    """

    for pdf_path in pdf_files[:1]:
        answers = gemini.ask_pdf(question, pdf_path, model="gemini-2.0-flash-exp")
        if answers:
            print(answers)
