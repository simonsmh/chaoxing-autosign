import asyncio
import json
import logging
import os
import re
import sys
import threading
import time

import aiohttp
import schedule
from bs4 import BeautifulSoup

logging.basicConfig(
    format="%(asctime)s - %(filename)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger("Chaoxing Autosign")


async def sign_user(loop, username, password, schoolid):
    async def sign_task(course_name, course_id, class_id):
        async def sign(task):
            async with s.get(
                "https://mobilelearn.chaoxing.com/widget/sign/pcStuSignController/preSign",
                params={
                    "activeId": task,
                    "courseId": course_id,
                    "classId": class_id,
                    "fid": schoolid,
                },
            ) as resp:
                sign = await resp.text()
            sign_soup = BeautifulSoup(sign, "lxml")
            result = sign_soup.select("span.greenColor")[0].text
            logger.info(f"{name}: {course_name}: {task} {result}")
            return result

        async with s.get(
            "https://mobilelearn.chaoxing.com/widget/pcpick/stu/index",
            params={"courseId": course_id, "jclassId": class_id},
        ) as resp:
            task_page = await resp.text()
        task_soup = BeautifulSoup(task_page, "lxml")
        task_list = [
            re.search(r"activeDetail\((\d+),", tasks.get("onclick")).group(1)
            for tasks in task_soup.select("div#startList [onclick$=',2,null)']")
        ]
        if task_list:
            logger.info(f"{name}: {course_name}: {task_list}")
            tasks = [sign(task) for task in task_list]
            await asyncio.gather(*tasks)
        else:
            logger.info(f"{name}: {course_name}: 无签到任务")
        return

    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.87 Safari/537.36"
    }
    async with aiohttp.ClientSession(headers=headers) as s:
        async with s.get(
            "http://passport2.chaoxing.com/api/login",
            params={"name": username, "pwd": password, "schoolid": schoolid},
        ) as resp:
            login = await resp.json(content_type=None)
        name = login.get("uname")
        logger.info(f"{name}: {login}")
        async with s.get("http://mooc1-2.chaoxing.com/visit/interaction") as resp:
            home = await resp.text()
        home_soup = BeautifulSoup(home, "lxml")
        course_id = [
            course.get("value") for course in home_soup.select("[name=courseId]")
        ]
        class_id = [
            course.get("value") for course in home_soup.select("[name=classId]")
        ]
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


def main(configs):
    loop = asyncio.new_event_loop()
    tasks = [
        sign_user(
            loop, config.get("USERNAME"), config.get("PASSWORD"), config.get("SCHOOLID")
        )
        for config in configs
    ]
    try:
        loop.run_until_complete(asyncio.gather(*tasks, loop=loop))
    except:
        pass
    finally:
        loop.close()


def run_threaded(job_func, args):
    job_thread = threading.Thread(target=job_func, args=[args])
    job_thread.start()


if __name__ == "__main__":
    if len(sys.argv) >= 2 and os.path.exists(sys.argv[1]):
        configs = load_json(sys.argv[1])
    else:
        configs = [
            {
                "SCHOOLID": int(input("学校 fid: ") or 25417),
                "USERNAME": input("学号: "),
                "PASSWORD": input("密码: "),
            }
        ]
    main(configs)
    logger.info("下次执行在5分钟之后")
    schedule.every(5).minutes.do(run_threaded, main, configs)
    while True:
        schedule.run_pending()
        time.sleep(1)
