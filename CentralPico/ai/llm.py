import urequests, ujson


class LLM:
    def __init__(self, url, key, model, system_prompt=None):
        self.url = url
        self.key = key
        self.model = model
        self.system_prompt = system_prompt

    def ask(self, prompt):
        url     = self.url
        headers = {
            "Content-Type":  "application/json",
            "Authorization": "Bearer " + self.key,
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user",   "content": prompt},
            ],
        }
        try:
            res    = urequests.post(url, data=ujson.dumps(payload).encode("utf-8"), headers=headers)
            result = res.json()
            res.close()
            if "choices" in result:
                return result["choices"][0]["message"]["content"].strip().replace("`", "")
            return "No choices"
        except Exception as e:
            print("LLM error:", e)
            return "LLM Error"
