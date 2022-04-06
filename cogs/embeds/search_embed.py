import numpy as np
from table2ascii import table2ascii as t2a, PresetStyle


class searchEmbed:
    def __init__(self, data, results):
        self.page = 0
        self.title = data['topic_name']
        self.relevanceResults = results
        self.upvotesResults = sorted(results, key=lambda d: d['votes_total'], reverse=True)

        self.results = self.relevanceResults
        self.pages = self.make_pages()
        self.show_pages()


    def make_pages(self) -> list:
        if len(self.results) == 0:
            return ["No results."]
        pages = []
        n = 5
        i = 0

        temp = []
        for i in range(len(self.results)):
            if i % n == 0 and i != 0:
                temp = np.array(temp)
                temp = temp.reshape(4, -1)
                temp = temp.tolist()
                temp = t2a(
                    header=["ID", "Topic Name", "Topic tags", "Votes"],
                    body=temp,
                    style=PresetStyle.thin_rounded,
                    first_col_heading=True,
                    last_col_heading=True
                )
                output = f"__**Results for \"{self.title}\"**__\n```{temp}```"
                pages.append(output)
                temp = []
            result = self.results[i]

            temp.append(result['topic_id'])
            temp.append(result['topic_name'])
            temp.append(', '.join(result['topic_tags']))
            temp.append(f"{result['votes_total']}")

        if i % n != n - 1 or i % n != 0:
            temp = np.array(temp)
            temp = temp.reshape(-1, 4)
            temp = temp.tolist()
            temp = t2a(
                header=["ID", "Topic Name", "Topic tags", "Votes"],
                body=temp,
                style=PresetStyle.thin_rounded,
                first_col_heading=True,
                last_col_heading=True
            )
            output = f"__**Results for '{self.title}'**__\n```{temp}```"
            pages.append(output)
            temp = []
        pages = [str(i) for i in pages]
        return pages

    def show_pages(self):
        self.description = self.pages[self.page]

    def previous_page(self):
        if self.page == 0:
            self.page = len(self.pages)
        self.page -= 1
        self.show_pages()

    def next_page(self):
        self.page += 1
        if self.page == len(self.pages):
            self.page = 0

        self.show_pages()

    def relevanceSort(self):
        self.page = 0
        self.results = self.relevanceResults
        self.pages = self.make_pages()
        self.show_pages()

    def upvotesSort(self):
        self.page = 0
        self.results = self.upvotesResults
        self.pages = self.make_pages()
        self.show_pages()
