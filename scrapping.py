import mongodb_data
import time
import requests
import gridfs
from selenium import webdriver
from bs4 import BeautifulSoup as bs
import pandas as pd
from pytube import YouTube
import logging
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By


logging.basicConfig(filename='loggers/loggers.txt', level=logging.INFO, format='%(asctime)s -- %(filename)s -- %(message)s')
logs=logging.getLogger()
def scroll_to_end(web_driver, interaction_time, no_of_videos = 0):
    '''

    :param web_driver:
    :param :
    :return:
    '''
    if no_of_videos > 0:
        total_scrolls_need = no_of_videos // 6
        scrolls = 0
    try:
        prev_h = 0
        while True:
            height = web_driver.execute_script("""
                            function getActualHeight() {
                                return Math.max(
                                    Math.max(document.body.scrollHeight, document.documentElement.scrollHeight),
                                    Math.max(document.body.offsetHeight, document.documentElement.offsetHeight),
                                    Math.max(document.body.clientHeight, document.documentElement.clientHeight)
                                );
                            }
                            return getActualHeight();
                        """)
            web_driver.execute_script(f"window.scrollTo({prev_h},{prev_h + 200})")
            # fix the time sleep value according to your network connection
            time.sleep(interaction_time)
            if no_of_videos > 0:
                scrolls += 1
                if scrolls > total_scrolls_need:
                    break
            prev_h += 200
            if prev_h >= height:
                break
    except Exception as e:
        logs.exception(e)



webdriver_path=Service(r'./chdriver/chromedriver')
def all_videos_page(channel_url:str, no_of_videos:int, interaction_time:int):
    '''

    :param no_of_videos:
    :param interaction_time:
    :return:
    '''
    _videos_title = []
    total_videos_urls = []
    videos_id = []
    videos_thumbnail = []
    try:
        if channel_url.strip("/"[-1]) != "videos":
            channel_url=channel_url+"/videos"
            logs.info("channel_url = %s",channel_url)
        driver = webdriver.Chrome(service=webdriver_path)
        driver.get(channel_url)
        time.sleep(interaction_time)
        driver.maximize_window()
        time.sleep(interaction_time)
        scroll_to_end(driver, interaction_time+1, no_of_videos)
        channel_video_page = driver.page_source.encode('utf-8').strip() # it will get the page_souse from the url
        driver.close()
        # load page in beautfyway  with the help of beautyfull soup
        soup = bs(channel_video_page, 'lxml')

        # creating variable for storing a scraped data
        channel_name = ""
        channel_subscribers = ""
        profile_picture_url = ""

        # taking channel name
        try:
            channel_name = soup.find("yt-formatted-string",{"class":"style-scope ytd-channel-name"}).text
            logs.info("channel name scrapped successfully")
        except Exception as e:
            logs.exception(e)

        # scrapping total subscribers
        try:
            channel_subscribers = soup.find("yt-formatted-string",id="subscriber-count").text
            logs.info("total subscribers scrapped successfully")
        except Exception as e:
            logs.exception(e)

        # scrapping youtuber profile picture
        try:
            profile_picture_url_ele = soup.find("div", id="channel-header-container")
            profile_picture_url = profile_picture_url_ele.find("img", {"class":"style-scope yt-img-shadow"}).get("src").split("=")[0]
            logs.info("youtuber profile picture scrapped successfully")
        except Exception as e:
            logs.exception(e)

        # scrapping titles of the videos
        try:
            title_page_ele = soup.findAll('a', id="video-title")
            # if no_of_ videos on the channel is less than the user ask for
            logs.info("no_of_videos by user want -- %s", no_of_videos)
            logs.info("total videos on the channel -- %s", len(title_page_ele))
            if no_of_videos > len(title_page_ele):
                no_of_videos = len(title_page_ele)
                logs.info("now no of videos is modified by total videos on the channel -- %s", no_of_videos)
            for i in range(no_of_videos):
                _videos_title.append(title_page_ele[i].get("title"))
            logs.info("Videos title scrapped successfully")
        except Exception as e:
            logs.exception(e)


        # scrapping videos id and url
        try:
            '''we get href like that ('/watch?v=r0FdMhMK4E4') so need to add the
            'https://www.youtube.com' before href so be get proper url of the video
            and for getting an id we use split function.
            '''
            title_page_ele = title_page_ele
            yt_url="https://www.youtube.com"
            for i in range(no_of_videos):
                href = title_page_ele[i].get("href")
                proper_url = "https://www.youtube.com"+href
                total_videos_urls.append(proper_url)
                videos_id.append(href[-11:])
            logs.info("videos_url and videos id scrapped successfully")
        except Exception as e:
            logs.exception(e)

        # scrapping a thumbnail of each video
        try:
            thumbnail_elements = soup.findAll('a', id="thumbnail")
            for i in range(1, no_of_videos+1):
                videos_thumbnail.append(thumbnail_elements[i].find("img", id="img").get("src").split("?")[0])
            logs.info("thumbnail scrapped successfully")
        except Exception as e:
            logs.exception(e)

    except Exception as e:
        logs.exception(e)

    try:
        all_videos_page_hashmap = {"Videos_url": total_videos_urls, "Videos_ID": videos_id, "Videos_Thumbnail": videos_thumbnail}
        all_videos_page_data = pd.DataFrame(all_videos_page_hashmap)
        all_videos_page_data.to_csv("all_videos_page_data.csv", index=False)
        logs.info("all_videos_page_data.csv csv file created successfully")
    except Exception as e:
        print(e)

    return [_videos_title, total_videos_urls, videos_thumbnail]





def each_video_info(interaction_time:int):
    '''
    :param
    :return:
    '''
    logs.info("inside a each_video_info")
    df1 = pd.read_csv("all_videos_page_data.csv")
    logs.info("reading csv file")
    videos_url_list = df1.Videos_url
    logs.info("videos urls logged in each_video_info function")
    total_likes = []
    total_views = []
    comments_count = []
    commenters_names = {}
    comments = {}
    try:

        # iterate list of all_videos urls
        for ind, url in enumerate(videos_url_list):
            logs.info("%s, --%s", ind, url)
            # using an YouTube class from pytube library
            for_pytube = YouTube(url)

            driver = webdriver.Chrome(service=webdriver_path)
            driver.get(url)
            driver.maximize_window()
            time.sleep(0.5)
            scroll_to_end(driver, interaction_time)
            if url.split("/")[3] == "shorts":
                logs.info("now in if, %s", ind)
                # finding the comment button for (yt shorts videos)
                comment_button = driver.find_element(By.CSS_SELECTOR, '#comments-button')
                # clicking on the comments button for getting an comments and commenters names
                comment_button.click()
                time.sleep(interaction_time)
                # // now execute query which actually will scroll until that element is not appeared on page
                # driver.execute_script("arguments[0].scrollIntoView();", button)
                soup = bs(driver.page_source, 'html.parser')
                driver.close()

                # scrapping likes of yt shorts
                like = soup.select('#text')[5].text
                total_likes.append(like)
                # scrapping comments of yt shorts
                comments_count.append(soup.select('#text')[7].text)
                # all_commenters_names element
                commenter_names_element = soup.select('#author-text span')
                list_of_commenter_names = [i.text.strip() for i in commenter_names_element]
                # all comments section
                comment_section_element = soup.select('#content #content-text')
                list_of_comments = [i.text for i in comment_section_element]
            else:
                logs.info("now in else, %s", ind)
                soup = bs(driver.page_source, 'html.parser')
                driver.close()

                likes = soup.select("#text")[2].text
                if not likes:
                    total_likes.append("None")
                else:
                    total_likes.append(likes)
                comment = soup.find('yt-formatted-string', {'class': 'count-text style-scope ytd-comments-header-renderer'}).text
                if not comment:
                    comments_count.append("None")
                else:
                    comments_count.append(comment)
                # all_commenters_names element
                commenter_names_element = soup.select('#author-text span')
                list_of_commenter_names = [i.text.strip() for i in commenter_names_element]
                # all comments section
                comment_section_element = soup.select('#content #content-text')
                list_of_comments = [i.text for i in comment_section_element]
            logs.info("out from else, %s", ind)

            # storing list of commenters names in commenters_name hashmap or dict
            commenters_names[str(ind)] = list_of_commenter_names
            # storing list of all_comments  in commenters hashmap/dict
            comments[str(ind)] = list_of_comments


            total_views.append(for_pytube.views)
    except Exception as e:
        logs.exception(e)
    #for key, value in commenters_names.items():
        #print(key, value)
    return [total_views, total_likes, comments_count, commenters_names, comments]


def fetching_all_data(url, videos, time):
    try:
        channel_name = url.split("/")[-1]
        data1 = all_videos_page(url, videos, time)
        logs.info("data1 scrapped successfully")
        logs.info("%s", data1)
        data2 = each_video_info(time)
        logs.info("%s", data2)

        all_information_sec = {"Title": data1[0], "Video_url": data1[1], "Thumbnail": data1[-1],
                               "Views": data2[0], "Likes": data2[1], "Comments_count": data2[2]
                               }
        mongodb_data.drop_old_data('{}'.format(channel_name))
        mongodb_data.upload_Videos_data('{}'.format(channel_name), all_information_sec)
        comments_sec = {"Commenters": data2[-2], "Comments": data2[-1]}
        coll_name = channel_name + " " + "Comments"
        mongodb_data.drop_old_data(coll_name)
        mongodb_data.upload_Comments_section(coll_name, comments_sec)
        return data1+data2
    except Exception as e:
        logs.exception(e)