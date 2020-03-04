import asyncio
import json
import logging
import os
import re
import sys
import time

import requests
import schedule
from bs4 import BeautifulSoup

logging.basicConfig(
    format="%(asctime)s - %(filename)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger("Chaoxing Autosign")


async def sign_user(loop, username, password, schoolid):
    s = requests.Session()
    s.headers.update(
        {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.87 Safari/537.36"
        }
    )

    async def sign_task(course_name, course_id, class_id):
        async def sign(task):
            sign = await loop.run_in_executor(
                None,
                lambda x: s.get(
                    x,
                    params={
                        "activeId": task,
                        "courseId": course_id,
                        "classId": class_id,
                        "fid": schoolid,
                    },
                ),
                "https://mobilelearn.chaoxing.com/widget/sign/pcStuSignController/preSign",
            )
            sign_soup = BeautifulSoup(sign.content, "lxml")
            result = sign_soup.select("span.greenColor")[0].text
            logger.info(f"{name}: {course_name}: {task} {result}")
            return result

        task_page = await loop.run_in_executor(
            None,
            lambda x: s.get(x, params={"courseId": course_id, "jclassId": class_id}),
            "https://mobilelearn.chaoxing.com/widget/pcpick/stu/index",
        )
        task_soup = BeautifulSoup(task_page.content, "lxml")
        task_list = [
            re.search(r"activeDetail\((\d+),", tasks.get("onclick")).group(1)
            for tasks in task_soup.select("div#startList [onclick]")
        ]
        if task_list:
            logger.info(f"{name}: {course_name}: {task_list}")
            tasks = [sign(task) for task in task_list]
            await asyncio.gather(*tasks)
        else:
            logger.info(f"{name}: {course_name}: 无签到任务")
        return

    login = s.get(
        "http://passport2.chaoxing.com/api/login",
        params={"name": username, "pwd": password, "schoolid": schoolid},
    )
    name = login.json().get("uname")
    logger.info(f"{name}: {login.json()}")
    home = s.get("http://mooc1-2.chaoxing.com/visit/interaction")
    home_soup = BeautifulSoup(home.content, "lxml")
    course_id = [course.get("value") for course in home_soup.select("[name=courseId]")]
    class_id = [course.get("value") for course in home_soup.select("[name=classId]")]
    course_name = [course.a.text for course in home_soup.select("h3.clearfix")]
    tasks = [
        sign_task(course_name[i], course_id[i], class_id[i])
        for i in range(len(course_id))
    ]
    await asyncio.gather(*tasks)


def load_json(filename="config.json"):
    try:
        with open(filename, "r") as file:
            config = json.load(file)
    except FileNotFoundError:
        try:
            filename = f"{os.path.split(os.path.realpath(__file__))[0]}/{filename}"
            with open(filename, "r") as file:
                config = json.load(file)
        except FileNotFoundError:
            logger.exception(f"Cannot find {filename}.")
            sys.exit(1)
    logger.info(f"Json: Loaded {filename}")
    return config


def main():
    if len(sys.argv) >= 2 and os.path.exists(sys.argv[1]):
        configs = load_json(sys.argv[1])
    else:
        configs = load_json()
    loop = asyncio.new_event_loop()
    tasks = [
        sign_user(
            loop, config.get("USERNAME"), config.get("PASSWORD"), config.get("SCHOOLID")
        )
        for config in configs
    ]
    loop.run_until_complete(asyncio.gather(*tasks, loop=loop))
    loop.close()


if __name__ == "__main__":
    main()
    schedule.every(5).minutes.do(main)
    while True:
        schedule.run_pending()
        time.sleep(1)
