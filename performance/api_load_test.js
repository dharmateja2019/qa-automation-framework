import http from "k6/http";
import { check, sleep, group } from "k6";

export const options = {
  stages: [
    { duration: "10s", target: 10 },
    { duration: "20s", target: 10 },
    { duration: "10s", target: 0 },
  ],
  // thresholds: {
  //   http_req_duration: ["p(95)<10"], // 10ms — impossible to meet
  //   http_req_failed: ["rate<0.01"],
  // },
  thresholds: {
    "http_req_duration{name:get_post}": ["p(95)<400"],
    "http_req_duration{name:list_posts}": ["p(95)<600"],
    http_req_failed: ["rate<0.01"],
  },
};

export default function () {
  group("get single post", () => {
    const res = http.get("https://jsonplaceholder.typicode.com/posts/1", {
      tags: { name: "get_post" },
    });
    check(res, { "status 200": (r) => r.status === 200 });
  });

  group("list all posts", () => {
    const res = http.get("https://jsonplaceholder.typicode.com/posts", {
      tags: { name: "list_posts" },
    });
    check(res, {
      "status 200": (r) => r.status === 200,
      "has 100 posts": (r) => JSON.parse(r.body).length === 100,
    });
  });

  sleep(1);
}
