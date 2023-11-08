import time
from typing import Any

from omegaconf import OmegaConf
from playwright.sync_api import sync_playwright
from pydantic import BaseModel, Field, HttpUrl, field_validator, model_validator


class CrawlerSettings(BaseModel):
    headless: bool = Field(default=False)


class CrawlerElements(BaseModel):
    username_element: str = Field(default="input[name='loginKey']")
    password_element: str = Field(default="input[name='password']")
    login_btn_element: str = Field(default="button:has-text('登入')")


class UserSettings(BaseModel):
    website: HttpUrl
    username: str
    password: str


class Config(BaseModel):
    user: UserSettings
    engine: CrawlerSettings
    elements: CrawlerElements


class WebCrawler(BaseModel):
    playwright: Any
    config: Config

    def login(self):
        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto(str(self.config.user.website))

        page.fill(self.config.elements.username_element, self.config.user.username)
        page.fill(self.config.elements.password_element, self.config.user.password)

        login_button_selector = self.config.elements.login_btn_element
        page.wait_for_selector(login_button_selector, state="visible")
        with page.expect_navigation():
            page.click(login_button_selector)

        try:
            page.wait_for_selector(
                self.config.elements.login_indicator_selector, state="visible", timeout=10000
            )
            print("登入成功")
        except Exception:
            print("登入失敗")
        finally:
            browser.close()


if __name__ == "__main__":
    with sync_playwright() as playwright:
        config_dict = OmegaConf.load("./configs/config.yaml")
        config_dict = OmegaConf.to_container(config_dict, resolve=True)
        config = Config(
            user=UserSettings(**config_dict["user_settings"]),
            engine=CrawlerSettings(**config_dict["crawler_settings"]),
            elements=CrawlerElements(**config_dict["crawler_elements"]),
        )
        crawler = WebCrawler(playwright=playwright, config=config)
        crawler.login()
