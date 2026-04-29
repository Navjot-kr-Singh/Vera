import json
import os

DB_FILE = os.path.join(os.path.dirname(__file__), "db.json")

class StateManager:
    """
    Handles persistence of contexts (Category, Merchant, Customer, Trigger)
    pushed by the judge.
    """
    def __init__(self):
        self.data = self._load()

    def _load(self):
        if os.path.exists(DB_FILE):
            try:
                with open(DB_FILE, "r") as f:
                    return json.load(f)
            except:
                pass
        return {
            "categories": {},
            "merchants": {},
            "customers": {},
            "triggers": {}
        }

    def save(self):
        with open(DB_FILE, "w") as f:
            json.dump(self.data, f, indent=2)

    def upsert_context(self, scope, context_id, payload):
        if scope == "category":
            self.data["categories"][context_id] = payload
        elif scope == "merchant":
            self.data["merchants"][context_id] = payload
        elif scope == "customer":
            self.data["customers"][context_id] = payload
        elif scope == "trigger":
            self.data["triggers"][context_id] = payload
        self.save()

    def get_category(self, slug):
        return self.data["categories"].get(slug, {})

    def get_merchant(self, mid):
        return self.data["merchants"].get(mid, {})

    def get_customer(self, cid):
        return self.data["customers"].get(cid, {})

    def get_trigger(self, tid):
        return self.data["triggers"].get(tid, {})

    def find_customer_for_merchant(self, mid):
        # Simplistic lookup for the first customer found for this merchant
        for cid, cust in self.data["customers"].items():
            if cust.get("merchant_id") == mid:
                return cust
        return None
