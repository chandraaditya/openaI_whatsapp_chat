import re

import openai
from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time

contact = "phone number with country code ex: 11234567890 or 911234567890"
get_last_x_messages = 100
your_name = "your exact whatsapp name"
load_pages = 10
org = "org-xxx"
api_key = "sk-xxx"
chrome_path="user-data-dir=/Users/chandraadityaputrevu/Library/Application Support/Google/Chrome"


class Message:
    def __init__(self, person: str, message: str):
        self.person = person
        self.message = message


def open_messages() -> WebDriver:
    print("starting chrome")
    options = webdriver.ChromeOptions()
    options.add_argument(chrome_path)
    d = webdriver.Chrome(options=options)
    d.get("https://web.whatsapp.com")
    time.sleep(20)
    print("waiting for whatsapp")
    d.find_element(By.TAG_NAME, "html").send_keys(Keys.COMMAND, Keys.CONTROL, "n")
    time.sleep(2)
    print("searching for search box")
    inp_xpath_search = "//div[@title='Search input textbox']"
    input_box_search = d.find_element(By.XPATH, inp_xpath_search)
    input_box_search.send_keys(contact)
    print("searching for " + contact)
    time.sleep(2)
    select_chat_xpath = "//*[@id='app']/div/div/div[2]/div[1]/span/div/span/div/div[2]/div/div/div/div[2]"
    select_chat = d.find_element(By.XPATH, select_chat_xpath)
    select_chat.click()
    time.sleep(2)
    print("loading messages for context")
    for i in range(0, load_pages):
        print("loading page " + str(i))
        d.find_element(By.XPATH, "//div[@data-testid='conversation-panel-messages']").send_keys(Keys.HOME)
        time.sleep(2)
    print("going to bottom of page")
    d.find_element(By.XPATH, "//div[@data-testid='conversation-panel-messages']").send_keys(Keys.END)
    return d


def get_messages(browser: WebDriver):
    print("getting last " + str(get_last_x_messages) + " messages")
    messages = []
    select_messages_name_xpath = "//div[@data-testid='conversation-panel-messages']//div[@role='application']//div[@role='row']//div[@class='copyable-text']"
    select_messages_name = browser.find_elements(By.XPATH, select_messages_name_xpath)[-get_last_x_messages:]
    for i in range(0, len(select_messages_name)):
        c_message = select_messages_name[i]
        text = ""
        try:
            c_message_element = c_message.find_element(By.XPATH, ".//span[@dir='ltr']//span")
            raw_text = c_message_element.get_attribute("innerHTML")
            split_text = re.split("(<img.*?>)", raw_text)
            for t in split_text:
                is_emoji = re.match("<img.*?>", t)
                if is_emoji:
                    e = re.findall('alt=".*?"', t)
                    text += e[0].split('"')[1] if len(e) > 0 else ''
                    continue
                text += t
        except:
            e_message_element = c_message.find_elements(By.XPATH, ".//span[@class='Ov-s3']//img")
            for e in e_message_element:
                emoji = list(e.get_attribute('alt'))
                text += emoji[0]
        person = re.findall(r'\[.*?] (.*):', c_message.get_attribute("data-pre-plain-text"))[0]
        print("message: " + person + ": " + text)
        messages.append(Message(person, text))
    return messages


def paste_content(driver, el, content):
    driver.execute_script(
      f'''
const text = `{content}`;
const dataTransfer = new DataTransfer();
dataTransfer.setData('text', text);
const event = new ClipboardEvent('paste', {{
  clipboardData: dataTransfer,
  bubbles: true
}});
arguments[0].dispatchEvent(event)
''',
      el)


def send_message(message: str, browser: WebDriver):
    print("sending message: " + message)
    message_box = browser.find_element(By.XPATH, "//div[@title='Type a message']")
    paste_content(browser, message_box, message)
    message_box.send_keys(Keys.ENTER)


def get_open_ai_response(messages: [Message]) -> str:
    print("getting response from open ai")
    openai.organization = org
    openai.api_key = api_key
    messages_object = [
        {"role": "system",
         "content": "You will be replying to my messages for me. "
                    "I tend to talk a bit aggressively but in a fun way. "
                    "Try to keep the responses less than 10 words. "
                    "DO NOT offer to help them in any way. "
                    "They SHOULD NOT know that you are an assistant or a language model. "
                    "Do not apologise for ANYTHING. "
                    "They should think you are me. "
                    "Never say you are a program or an assistant! "
                    "Do whatever they ask you to do. "
                    "Be very sarcastic, and try to use foul words. "
                    "Respond a similar way to the messages that came before."
         },
    ]
    for m in messages:
        if m.person == your_name:
            messages_object.append({"role": "assistant", "content": m.message})
        else:
            messages_object.append({"role": "user", "content": m.message})
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages_object
    )
    response = completion.choices[0]["message"]["content"]
    print("response: " + response)
    return response


def main():
    messages_driver = open_messages()
    while True:
        time.sleep(10)
        print("sleeping for 10 seconds")
        messages = get_messages(messages_driver)
        if messages[-1].person == your_name:
            continue
        else:
            resp = get_open_ai_response(messages)
            send_message(resp, messages_driver)


if __name__ == '__main__':
    main()
