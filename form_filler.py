import logging
import random
from concurrent.futures import ThreadPoolExecutor
import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from xvfbwrapper import Xvfb
from threading import Lock, Event

class FormFiller:
    def __init__(self):
        self.total_iterations = 0
        self.responses_sent = 0
        self.errors = 0
        self.iterations_left = 0
        self.stop_flag = Event()
        self.lock = Lock()
        self.environment_status = []

    def fill_form(self, url, num_iterations, update_callback=None, environment_id=1):
        self.stop_flag.clear()
        display = None
        driver = None

        try:
            # Start Xvfb display
            display = Xvfb(width=1280, height=720)
            display.start()

            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")

            driver = webdriver.Chrome(options=chrome_options)
            driver.get(url)

            for _ in range(num_iterations):
                if self.stop_flag.is_set():
                    break

                try:
                    # Handling radio buttons
                    radio_buttons = driver.find_elements(By.CSS_SELECTOR, 'div[role="radiogroup"]')
                    for radio_group in radio_buttons:
                        options = radio_group.find_elements(By.CSS_SELECTOR, 'div[role="radio"]')
                        # Use weighted random choice to add more randomness
                        random.choice(options).click()

                    # Handling checkboxes
                    checkboxes = driver.find_elements(By.CSS_SELECTOR, 'div[role="checkbox"]')
                    for checkbox in checkboxes:
                        if random.random() < 0.5:  # 50% chance to click a checkbox
                            checkbox.click()

                    # Handling multiple choice grids
                    grids = driver.find_elements(By.CSS_SELECTOR, 'div[role="grid"]')
                    for grid in grids:
                        rows = grid.find_elements(By.CSS_SELECTOR, 'div[role="row"]')
                        for row in rows:
                            options = row.find_elements(By.CSS_SELECTOR, 'div[role="radio"]')
                            # Shuffle options before making a random selection to increase randomness
                            random.shuffle(options)
                            random.choice(options).click()

                    # Submit the form
                    submit = driver.find_element(By.CSS_SELECTOR, 'div[role="button"]')
                    submit.click()

                    logging.info(f"Form submitted successfully by Environment {environment_id}")

                    with self.lock:
                        self.responses_sent += 1
                        self.iterations_left = self.total_iterations - self.responses_sent
                        self.environment_status.append(
                            f"Environment {environment_id}: Total Responses Sent: {self.responses_sent}, Errors: {self.errors}, Iterations Left: {self.iterations_left}"
                        )

                    # Wait and reload the form
                    time.sleep(random.uniform(3, 7))  # Vary the wait time to add randomness
                    driver.get(url)

                except Exception as e:
                    with self.lock:
                        self.errors += 1
                        self.iterations_left = self.total_iterations - self.responses_sent
                        self.environment_status.append(
                            f"Environment {environment_id}: Error occurred: {e}"
                        )
                    logging.error(f"Error occurred in Environment {environment_id}: {e}")

        finally:
            if driver:
                driver.quit()
            if display:
                if 'DISPLAY' in os.environ:
                    display.stop()

    def stop(self):
        self.stop_flag.set()

    def fill_form_in_parallel(self, url, total_iterations, update_callback=None):
        self.total_iterations = total_iterations
        self.iterations_left = total_iterations
        self.responses_sent = 0
        self.errors = 0
        self.environment_status = []

        num_envs = 10  # Total number of environments to run concurrently
        iterations_per_env = total_iterations // num_envs  # Each environment should process its share of iterations

        with ThreadPoolExecutor(max_workers=num_envs) as executor:
            futures = []
            for i in range(num_envs):
                futures.append(executor.submit(self.fill_form, url, iterations_per_env, update_callback, i + 1))

            for future in futures:
                future.result()

        # Handle remaining iterations
        remaining_iterations = total_iterations % num_envs
        if remaining_iterations > 0:
            with ThreadPoolExecutor(max_workers=remaining_iterations) as executor:
                futures = []
                for i in range(remaining_iterations):
                    futures.append(executor.submit(self.fill_form, url, 1, update_callback, i + 1))
                for future in futures:
                    future.result()
