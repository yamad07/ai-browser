import asyncio
from typing import List
from playwright.async_api import async_playwright
from unstructured.partition.html import partition_html
from langchain.prompts import (
    PromptTemplate,
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI
from pydantic import BaseModel, Field, validator
from langchain.output_parsers import PydanticOutputParser


class SearchedPage2Json:
    async def load_with_playwright(url: str):
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url)

            remove_selectors = ["header", "footer"]
            for selector in remove_selectors or []:
                elements = await page.locator(selector).all()
                for element in elements:
                    if await element.is_visible():
                        await element.evaluate("element => element.remove()")
        
            elements = await page.locator("a").all()
            for element in elements:
                if await element.is_visible():
                    await element.evaluate("""e => e.innerHTML = `url: ${e.href} ${e.innerText}`;""")

            pgc = await page.content()

            page_source = await page.content()
            elements = partition_html(text=page_source)
            text = "\n\n".join([str(el) for el in elements])

            return text

class SearchedPage(BaseModel):
    url: str = Field(description="linked page url")
    title: str = Field(description="linked page title")
    description: str = Field(description="description or partial excerpts from linked pages")

class SearchedPageList(BaseModel):
    query: str = Field(description="searched keywords")
    pages: List[SearchedPage] = Field(description="searched result page list")

if __name__ == "__main__":
    # asyncio.run(load_with_playwright("https://www.google.com/search?q=精神現象学&oq=%E7%B2%BE%E7%A5%9E%E7%8F%BE%E8%B1%A1%E5%AD%A6&aqs=chrome..69i57.4398j0j1&sourceid=chrome&ie=UTF-8"))

    llm_query = "「Pyhton」とGoogle検索したときに返されそうな結果リストのダミー"

    parser =  PydanticOutputParser(pydantic_object=SearchedPageList)

    prompt = PromptTemplate(
        template="Answer the user query. \n{format_instructions}\n{query}\n",
        input_variables=["query"],
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )

    llm = ChatOpenAI(temperature=0)
    _input = prompt.format_prompt(query=llm_query)

    output = llm(_input.to_messages())
    print(parser.parse(output.content))
