# locustfile.py
"""
Locust load test example for public testing endpoints (httpbin.org).
Intended for testing and learning only. Do NOT use this against sites
you don't own or don't have permission to test.
"""

from locust import HttpUser, task, between, LoadTestShape, events
import random
import string
import time
import json

def random_string(n=8):
    return "".join(random.choices(string.ascii_letters + string.digits, k=n))

class BasicUser(HttpUser):
    # use between to simulate think time
    wait_time = between(1, 5)

    @task(6)
    def get_root(self):
        # simple GET (cacheable path)
        self.client.get("/get", name="GET /get", timeout=30)

    @task(3)
    def get_with_query(self):
        # GET with randomized query parameters
        params = {"q": random_string(6), "page": random.randint(1, 100)}
        self.client.get("/get", params=params, name="GET /get?q=..", timeout=30)

    @task(2)
    def delayed(self):
        # endpoint that sleeps before responding - useful to simulate backend latency
        # try /delay/1, /delay/2 (seconds)
        delay = random.choice([1, 2, 3])
        self.client.get(f"/delay/{delay}", name=f"GET /delay/{delay}", timeout=60)

    @task(2)
    def stream(self):
        # streaming endpoint (returns multiple lines)
        self.client.get("/stream/20", name="GET /stream/20", timeout=60)

    @task(3)
    def post_json(self):
        # POST with JSON body
        payload = {
            "id": random.randint(1, 100000),
            "name": random_string(10),
            "timestamp": int(time.time())
        }
        self.client.post("/post", json=payload, name="POST /post (json)", timeout=30)

    @task(1)
    def status_check(self):
        # occasionally check for non-200 statuses
        code = random.choice([200, 200, 200, 404, 500])  # mostly 200, sometimes errors
        self.client.get(f"/status/{code}", name=f"GET /status/{code}", timeout=30)


# Optional: step load shape to ramp up users in steps
class StepLoadShape(LoadTestShape):
    """
    Step load shape:
      - step_duration: seconds per step
      - step_users: users to add each step
      - hold_steps: number of steps to hold (after ramp) before ramping down
    Example: step_duration=60, step_users=20, max_steps=6 -> ramp to 120 users in 6 minutes
    """
    step_duration = 60
    step_users = 20
    max_steps = 6
    hold_steps = 2  # how many steps to hold at peak before stopping

    def tick(self):
        run_time = self.get_run_time()
        total_ramp_time = self.step_duration * self.max_steps
        if run_time > total_ramp_time + (self.hold_steps * self.step_duration):
            # returning None will stop the test
            return None

        if run_time <= total_ramp_time:
            # ramp-up phase
            current_step = int(run_time // self.step_duration) + 1
            target_users = current_step * self.step_users
            spawn_rate = max(1, int(self.step_users / 5))
            return (target_users, spawn_rate)
        else:
            # holding at peak
            target_users = self.max_steps * self.step_users
            spawn_rate = max(1, int(self.step_users / 5))
            return (target_users, spawn_rate)


# Good to log when test stops (optional)
@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    print("Test finished. Summary:")
    stats = environment.runner.stats
    # print some high-level stats (if runner exists)
    if environment.runner:
        print(f"  Total requests: {stats.total.num_requests}")
        print(f"  Failures: {stats.total.num_failures}")
        print(f"  Avg response time (ms): {stats.total.avg_response_time}")
