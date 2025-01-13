from abc import ABC, abstractmethod
import os
class PROMPT_CLASS(ABC):
    def __init__(self):
        self.transcript = None
    
    @abstractmethod
    def messages():
        pass


    def update(self, transcript, **kwargs):
        self.transcript = transcript


class FIVE_SCORING(PROMPT_CLASS):
    def __init__(self):
        super().__init__()
        self.company_name = None


    def update(self, transcript, **kwargs):
        super().update(transcript, **kwargs)
        self.company_name = kwargs.get("company_name", self.company_name)
        

    def messages(self):
        assert self.transcript is not None, "Transcript is not set"
        assert self.company_name is not None, "Company name is not set"
        system_msg = """
        Role: You are a top-tier financial analyst specialized in interpreting earnings transcripts and anticipating their likely impact on a company’s stock over the next 1–2 weeks.
        Objective:

        Analysis: Thoroughly review the earnings transcript, focusing on short-term (1–2 weeks) implications. Consider factors such as company performance vs. expectations, management’s tone, guidance updates, and any external/macro influences.
        Conclusion: Predict the short-term (1–2 weeks) impact on the stock price.
        Rating: Return one numeric rating at the end on a separate line with enclosed in qquare brackets according to this scale:
        2: Great positive impact (stock will rally)
        1: Positive impact
        0: No impact or neutral
        -1: Negative impact
        -2: Great negative impact (stock will fall)
        Instructions:

        Provide a concise explanation (2–3 sentences) describing your main reasoning.
        End your response with only the numeric rating on its own line (e.g., 2).
        Do not include disclaimers or legal statements.
        No additional information will be provided.
        """
        user_msg =  f"""
        Transcript for {self.company_name}:
        {self.transcript['content']}
        """

        user_example = """
        Transcript for 3M Company:
        Executives Joel Moskowitz (CEO), Jerry Pellizzon (CFO), David Reed (President, North American Operations), and Michael Kraft (President, Nuclear and Semiconductor Products) hosted Ceradyne's 2007 Q4 and full-year results call. Analysts included Pierre Maccagno (Needham), Al Kaschalk (Wedbush), Josephine Millward (Stanford), Gary Liebowitz (Wachovia), Jason Simon (JMP), Michael French (Morgan Joseph), and Ferat Ongoren (Citigroup). Moskowitz detailed financial results, highlighting $191.4M Q4 sales, $35.2M net income, and a $756.8M annual record, despite a challenging stock market. Updates included delays in XSAPI/ESAPI military contracts, a reduced 2008 body armor forecast, and optimistic growth in solar ceramics and non-defense markets. Notable expansions are underway in China and Germany. Guidance for 2008 projects $715M-$836M sales and $4.55-$5.05 EPS. The team addressed cost-saving measures, potential acquisitions, and ongoing diversification efforts, targeting $1B+ revenue by 2010. Key concerns included MRAP II opportunities, LTAS certification progress, and ESK subsidiary performance. Ceradyne continues pursuing strategic growth while managing defense market uncertainties.
        """

        assistent_msg = f"""Ceradyne’s Q4 and full-year earnings call revealed mixed signals. While the company achieved record annual sales, the lowered 2008 guidance, delays in military contracts, and reduced body armor forecasts signal short-term headwinds. However, management’s focus on non-defense market growth, cost-cutting measures, and strategic expansions in solar ceramics and manufacturing suggest long-term potential. The stock is likely to face short-term pressure due to tempered guidance and uncertainties around key defense contracts.
[-1]
        """


        return [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_example},
            {"role": "assistant", "content": assistent_msg},
            {"role": "user", "content": user_msg},
        ]
    
    def check_exists(self, file_output_name):
        # check if exists
        # data/{symbol}/{class_name}/{trascnript['date']}.txt
        symbol = self.transcript['symbol']
        class_name = self.__class__.__name__
        file_name = f"data/{symbol}/{class_name}/{file_output_name}/{self.transcript['date']}.txt"
        return os.path.exists(file_name)

    
    def process_response(self, response,file_output_name):
        if response.choices is None:
            return
        symbol = self.transcript['symbol']
        # create  folder with the name of the class if it does not exist
        class_name = self.__class__.__name__
        os.makedirs(f"data/{symbol}/{class_name}/{file_output_name}", exist_ok=True)

        for recommandations in response.choices:
            with open(f"data/{symbol}/{class_name}/{file_output_name}/{self.transcript['date']}.txt", "w") as file:
                file.write(recommandations.message.content)
