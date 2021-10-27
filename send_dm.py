from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from getpass import getpass
import time
import random
import schedule


class Auto_IG():

    def __init__(self):
        self.username = "username"
        self.PATH = "/usr/local/bin/chromedriver"
        self.options = Options().add_argument(
            '--user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 13_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/92.0.4515.159 Mobile/15E148 Safari/604.1')
        # "user-data-dir=selenium"
        self.browser = webdriver.Chrome(self.PATH, chrome_options=self.options)
        self.login_url = "https://www.instagram.com/accounts/login/"
        self.dm_url = "https://www.instagram.com/direct/new/"
        self.timee = "10:00"
        self.usernames = [x.split()[0]
                          for x in open("djs_followers.txt", 'r+').readlines()]
        self.message_options = {"one": ["Hello", "Hi", "Hey there", "Hi there", "Hey", "Hello there"],
                                "two": ["my name is", "I’m",  "I am"],
                                "three": ["and", "&", "and the"],
                                "four": ["powerhouse", "startup", "business", "organization"],
                                "five": ["the technologies", "skills", "technology & tools"],
                                "six": ["I'm reaching out", "I wanted to reach out", "I reached out", "I decided to reach out"],
                                "seven": ["the engagement", "the activity", "the content", "the interaction"],
                                "eight": ["honored", "esteemed", "excited", "appreciative", "revered"],
                                "nine": ["influencer", "individual", "person", "character"],
                                "ten": ["share", "repost"],
                                "eleven": ["releasing", "delivering", "revealing", "broadcasting", "publicizing"],
                                "twelve": ["digital course content", "digital course", "digital learning offering", "digital offering", "online course offering", "online course"],
                                "thirteen": ["welcome", "accept", "appreciate", "encourage"],
                                "fourteen": ["spreading", "sharing", "giving out", "giving"],
                                "fifteen": ["Thank you", "Thanks’", "Thank you so much", "Thank-you", "Thanks"]
                                }
        pass

    def fetch_cookies(self):
        # global x
        # x = 0
        # username whom you will send the message

        # Step 4 of the installations instructions
        PATH = self.PATH
        browser = self.browser
        browser.get(self.login_url)

        time.sleep(4)

        usrname_bar = browser.find_element_by_name('username')
        passwrd_bar = browser.find_element_by_name('password')

        # Enter your username here
        username = self.username
        # Enter your password here
        password = getpass()

        usrname_bar.send_keys(username)
        passwrd_bar.send_keys(password + Keys.ENTER)

        time.sleep(4)

        pickle.dump(self.browser.get_cookies(), open("cookies.txt", "wb"))

    def load_cookies(self):

        cookies = pickle.load(open("cookies.txt", "rb"))
        self.browser.delete_all_cookies()
        self.browser.get(self.login_url)

        for cookie in cookies:
            self.browser.add_cookie(cookie)

    def login_with_cookies(self):
        self.load_cookies()
        self.browser.get(self.dm_url)

    def randomize_message(self, usernamee):

        message_options = self.message_options

        for options in message_options:
            random.shuffle(message_options[options])

        message = "{one} @{usernames}, {two} Dj, CEO {three} Founder of MoorNetworks — a TechEd {four} for learning {five} that helps one become an IT Engineer. {six} because I love {seven} on your platform and would be {eight} if an {nine} such as yourself could {ten} the post with your followers. As MoorNetworks get's closer to {eleven} its {twelve}, we would {thirteen} your hand in {fourteen} the word. {fifteen} in advance!".format(one=message_options["one"][0],
                                                                                                                                                                                                                                                                                                                                                                                                                                                       usernames=usernamee,
                                                                                                                                                                                                                                                                                                                                                                                                                                                       two=message_options[
            "two"][0],
            three=message_options[
            "three"][0],
            four=message_options[
            "four"][0],
            five=message_options[
            "five"][0],
            six=message_options[
            "six"][0],
            seven=message_options[
            "seven"][0],
            eight=message_options[
            "eight"][0],
            nine=message_options[
            "nine"][0],
            ten=message_options[
            "ten"][0],
            eleven=message_options[
            "eleven"][0],
            twelve=message_options[
            "twelve"][0],
            thirteen=message_options[
            "thirteen"][0],
            fourteen=message_options[
            "fourteen"][0],
            fifteen=message_options[
            "fifteen"][0]
        )

        return message

    def send_dm(self, usernamee):
        self.browser.get(self.dm_url)

        time.sleep(2)

        to_btn = self.browser.find_element_by_name('queryBox')
        to_btn.send_keys(usernamee)

        time.sleep(2)

        chk_mrk = self.browser.find_element_by_xpath(
            '/html/body/div[2]/div/div/div[2]/div[2]/div/div/div[3]/button/div')
        chk_mrk.click()

        time.sleep(2)

        nxt_btn = self.browser.find_element_by_class_name('rIacr')
        nxt_btn.click()

        time.sleep(2)

        txt_box = self.browser.find_element_by_tag_name('textarea')
        # Customize your message
        message = self.randomize_message(usernamee)
        txt_box.send_keys(message)

        time.sleep(1)

        snd_btn = self.browser.find_elements_by_css_selector(
            '.sqdOP.yWX7d.y3zKF')
        snd_btnn = snd_btn[len(snd_btn)-1]
        snd_btnn.click()

        time.sleep(2)
        pass

    def main(self):
        # x = 0
        count = 0
        self.login_with_cookies()
        try:
            for usrnamee in self.usernames:
                dm = schedule.every().day.at(self.timee).do(self.send_dm(usrnamee))
                count += 1

        except TypeError as a:
            print('Failed!', a)

        # quit = self.browser.quit()

        return (f'''
        Successfully Sent {count} Messages!
        ''')

        # x += 1

        timee = "12:58"  # Specific Time When The message will be send

        # try:

        #     self.login()
        # except TypeError:
        #     pass

        # try:
        #     while True and x != 1:
        #         # schedule.run_pending()
        #         time.sleep(1)
        # except UnboundLocalError:
        #     pass


if __name__ == "__main__":
    obj = Auto_IG()
    print(obj.main())

#         print('Your message was successful sent! :D\n')
