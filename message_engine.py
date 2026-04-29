import random
from datetime import datetime, timedelta, timezone
import json

class MessageEngine:
    def __init__(self):
        self.ist = timezone(timedelta(hours=5, minutes=30))
        # Category specific configurations
        self.category_config = {
            "restaurant": {
                "tones": ["craving", "delicious", "tasty", "fresh", "hot"],
                "emojis": ["🍔", "🍕", "🌮", "🤤", "🍽️"],
                "templates": [
                    "{urgency_prefix} {tone} {category}? {merchant_name} has {offer}! {cta}",
                    "Hungry? {merchant_name} is serving {tone} deals. Get {offer} {urgency_suffix}! {cta}",
                    "{urgency_prefix} Treat yourself to {merchant_name}. {offer} waiting for you! {cta}"
                ]
            },
            "salon": {
                "tones": ["glow up", "pamper", "refresh", "relax", "style", "premium"],
                "emojis": ["💅", "💇‍♀️", "✨", "💆‍♂️", "✂️"],
                "templates": [
                    "{urgency_prefix} Time for a {tone}! Get {offer} at {merchant_name}. {cta}",
                    "Treat yourself to a {tone} at {merchant_name}. {offer} {urgency_suffix}! {cta}",
                    "{urgency_prefix} Ready for a {tone}? {merchant_name} is offering {offer}. {cta}"
                ]
            },
            "grocery": {
                "tones": ["fresh", "essentials", "stock up", "savings", "pantry"],
                "emojis": ["🛒", "🥦", "🍞", "🍎", "🛍️"],
                "templates": [
                    "{urgency_prefix} Stock up on {tone} essentials! {merchant_name} gives you {offer}. {cta}",
                    "Need {tone} groceries? Get {offer} at {merchant_name} {urgency_suffix}! {cta}",
                    "{urgency_prefix} Save on {tone} items at {merchant_name} with {offer}! {cta}"
                ]
            },
            "fashion": {
                "tones": ["trendy", "style", "wardrobe", "look", "outfit"],
                "emojis": ["👗", "👕", "👠", "😎", "✨"],
                "templates": [
                    "{urgency_prefix} Upgrade your {tone} with {merchant_name}! Get {offer}. {cta}",
                    "Looking for a new {tone}? {merchant_name} has {offer} {urgency_suffix}! {cta}",
                    "{urgency_prefix} Step out in {tone}! {offer} at {merchant_name}. {cta}"
                ]
            },
            "dentist": {
                "tones": ["clinical", "oral health", "precision", "care", "wellness"],
                "emojis": ["🦷", "👨‍⚕️", "👩‍⚕️", "✨", "🏥"],
                "templates": [
                    "{urgency_prefix} {owner_prefix}Maintain peak clinical excellence at {merchant_name}{location_mention}. {offer} available now. {cta}",
                    "{urgency_prefix} {owner_prefix}New technical updates for your {tone} practice in {locality}. {offer} waiting! {cta}"
                ]
            },
            "default": {
                "tones": ["special", "exclusive", "amazing", "great"],
                "emojis": ["🎉", "🔥", "👇", "🚀", "💥"],
                "templates": [
                    "{urgency_prefix} Don't miss out! {merchant_name} is offering {offer}. {cta}",
                    "Looking for something {tone}? Get {offer} at {merchant_name} {urgency_suffix}! {cta}",
                    "{urgency_prefix} {merchant_name} has a {tone} deal: {offer}! {cta}"
                ]
            }
        }

        # Trigger specific configurations
        self.trigger_config = {
            "weekend": {"urgency_prefix": "Weekend Special!", "urgency_suffix": "this weekend", "tags": ["weekend", "leisure"]},
            "festival": {"urgency_prefix": "Festive Deal!", "urgency_suffix": "this festival season", "tags": ["festival", "celebration"]},
            "low sales": {"urgency_prefix": "Flash Sale!", "urgency_suffix": "today only", "tags": ["urgency", "discount", "flash-sale"]},
            "lunch time": {"urgency_prefix": "Lunch Hour Deal!", "urgency_suffix": "for lunch today", "tags": ["lunch", "time-sensitive"]},
            "rain": {"urgency_prefix": "Rainy Day Special!", "urgency_suffix": "while it rains", "tags": ["weather", "cozy"]},
            "payday": {"urgency_prefix": "Payday Treat!", "urgency_suffix": "this payday", "tags": ["payday", "splurge"]},
            "default": {"urgency_prefix": "Limited Time!", "urgency_suffix": "now", "tags": ["general"]}
        }

        self.customer_context = {
            "new user": "Welcome! ",
            "inactive": "We missed you! Come back for this: ",
            "repeat": "As a loyal customer, ",
            "high spender": "As a VIP, ",
            "default": ""
        }

    def _get_day_context(self):
        day = datetime.now(self.ist).weekday()
        if day in [5, 6]:
            return "weekend"
        return "weekday"

    def _score_message(self, message, trigger, offer):
        score = 50 # Base score
        message_lower = message.lower()
        
        # Urgency signals
        if "today" in message_lower or "now" in message_lower or "weekend" in message_lower or "hour" in message_lower:
            score += 20
        
        # CTA presence
        if "order" in message_lower or "visit" in message_lower or "get" in message_lower or "shop" in message_lower:
            score += 15
            
        # Offer details
        if "%" in offer or "off" in offer.lower() or "free" in offer.lower() or "bogo" in offer.lower():
            score += 10
            
        # Context matching
        if trigger.lower() in message_lower:
            score += 5
            
        return min(score, 100)

    def generate(self, category, merchant_name, offer, trigger, customer_type="", tone_style="default", boost_mode_id=None, full_context=None):
        category = category.lower() if category else "default"
        trigger = trigger.lower() if trigger else "default"
        customer_type = customer_type.lower() if customer_type else "default"
        tone_style = tone_style.lower() if tone_style else "default"

        cat_conf = self.category_config.get(category, self.category_config["default"])
        
        # Dynamic date handling - if no trigger is given but it's the weekend, infer weekend trigger
        if trigger == "default" and self._get_day_context() == "weekend":
            trigger = "weekend"
            
        trig_conf = self.trigger_config.get(trigger, self.trigger_config["default"])
        
        # Context weighting: Trigger > Merchant > Category > Customer
        # We apply this by making sure trigger prefixes are prominent, and customer context is optional but prepended
        cust_prefix = self.customer_context.get(customer_type, "")

        # Extract real data from full_context if available
        locality = ""
        owner_name = ""
        if full_context:
            merchant_data = full_context.get("merchant", {})
            if not merchant_name or merchant_name == "Your Business":
                merchant_name = merchant_data.get("identity", {}).get("name", merchant_name)
            locality = merchant_data.get("identity", {}).get("locality", "")
            owner_name = merchant_data.get("identity", {}).get("owner_first_name", "")
            
            # If offer is generic, try to pick an active offer from merchant context
            if not offer or offer == "great deals" or offer == "20% OFF":
                merchant_offers = merchant_data.get("offers", [])
                active_offers = [o for o in merchant_offers if o.get("status") == "active"]
                if active_offers:
                    offer = active_offers[0].get("title", offer)
        
        # Specificity boosts
        location_mention = f" in {locality}" if locality else ""
        
        if category == "dentist" or category == "dentists":
            owner_prefix = f"Dr. {owner_name}" if owner_name else "Dr."
        else:
            owner_prefix = owner_name if owner_name else ""
            
        owner_prefix_msg = f"Hi {owner_prefix}, " if owner_prefix else ""


        ctas = ["Order now!", "Visit today!", "Shop now!", "Tap to claim!", "Don't miss out!"]

        modes = [
            {"id": "aggressive", "name": "🔥 Aggressive", "urgency_boost": True, "premium_boost": False, "target_customer": customer_type},
            {"id": "premium", "name": "💎 Premium", "urgency_boost": False, "premium_boost": True, "target_customer": customer_type},
            {"id": "retention", "name": "🎯 Retention", "urgency_boost": True, "premium_boost": False, "target_customer": "inactive"},
            {"id": "growth", "name": "🚀 Growth", "urgency_boost": False, "premium_boost": False, "target_customer": "new user"}
        ]

        variations = []

        for mode in modes:
            # Adjust parameters based on mode
            current_customer = mode["target_customer"]
            cust_prefix = self.customer_context.get(current_customer, "")
            
            # Select template and tone based on mode
            if mode["premium_boost"] or current_customer == "high spender":
                tone = "exclusive" if category == "default" else "premium"
                emoji = "✨"
                template = "{urgency_prefix} {owner_prefix}Experience {tone} quality at {merchant_name}{location_mention}. {offer} {urgency_suffix}. {cta}"
                ctas_list = ["Book now", "Discover more", "Treat yourself"]
            elif mode["id"] == "aggressive":
                tone = random.choice(cat_conf["tones"])
                emoji = "🔥"
                template = "HURRY! {urgency_prefix} {owner_prefix}{merchant_name}{location_mention} has {offer} on {tone} items! {urgency_suffix}! {cta}"
                ctas_list = ["Shop NOW!", "Don't miss out!", "Claim fast!"]
            elif mode["id"] == "retention":
                tone = random.choice(cat_conf["tones"])
                emoji = "🎯"
                template = "{urgency_prefix} We miss you! Enjoy {offer} on {tone} favorites at {merchant_name}. {cta}"
                ctas_list = ["Come back today!", "Order now!"]
            else: # Growth
                tone = random.choice(cat_conf["tones"])
                emoji = "🚀"
                template = "{urgency_prefix} Discover {merchant_name}! Get {offer} on your first {tone} order. {cta}"
                ctas_list = ["Try us today!", "Welcome aboard!"]

            # Smart Timing Engine: Override content based on specific triggers
            if trigger == "lunch time":
                tone = "lunch"
                emoji = "🍲"
                template = "{urgency_prefix} Beat the mid-day cravings! Get {offer} on {tone} favorites at {merchant_name}. {cta}"
            elif trigger == "rain":
                tone = "comfort"
                emoji = "☔"
                template = "Stay dry! Enjoy {offer} on cozy {tone} items from {merchant_name} {urgency_suffix}. {cta}"
            elif trigger == "payday" and mode["id"] != "retention" and mode["id"] != "growth":
                tone = "premium"
                template = "You earned it! Treat yourself to {tone} experiences at {merchant_name}. {offer} {urgency_suffix}. {cta}"
                
            cta = random.choice(ctas_list)

            msg = template.format(
                urgency_prefix=trig_conf["urgency_prefix"],
                urgency_suffix=trig_conf["urgency_suffix"],
                tone=tone,
                category=category,
                merchant_name=merchant_name,
                offer=offer,
                cta=cta,
                owner_prefix=owner_prefix_msg,
                location_mention=location_mention,
                locality=locality
            )
            
            final_msg = f"{cust_prefix}{msg} {emoji}"
            
            # Apply Tone Personalization
            if tone_style == "genz":
                final_msg = final_msg.replace("Don't miss out", "No cap, this is fire 🔥")
                final_msg = final_msg.replace("HURRY", "FR FR 🏃‍♂️")
                final_msg = final_msg.replace("Treat yourself", "Treat yo self 💅")
                final_msg = final_msg.replace("Experience", "Vibe with")
                final_msg = final_msg.replace("Book now", "Lock it in 🔒")
                final_msg = final_msg.replace("Enjoy", "Vibe with")
                final_msg = final_msg.replace("Welcome", "Wsg")
                final_msg = final_msg.replace("Shop NOW", "Cop it now 🛒")
            elif tone_style == "hinglish":
                final_msg = final_msg.replace("Don't miss out", "Miss mat karo! 😱")
                final_msg = final_msg.replace("HURRY", "Jaldi aao!")
                final_msg = final_msg.replace("Treat yourself", "Khushiyan manao!")
                final_msg = final_msg.replace("Book now", "Abhi book karo!")
                final_msg = final_msg.replace("Shop NOW", "Abhi order karo!")
                final_msg = final_msg.replace("Welcome", "Swagat hai!")
                final_msg = final_msg.replace("Enjoy", "Maza lo")
                final_msg = final_msg.replace("Get ", "Pao ")
            elif tone_style == "professional":
                import re
                final_msg = re.sub(r'[^\w\s,!.?-]', '', final_msg)
                final_msg = final_msg.replace("HURRY!", "Time Sensitive:")
                final_msg = final_msg.replace("Don't miss out!", "We cordially invite you.")
                final_msg = final_msg.replace("Shop NOW!", "Explore our collection.")
                final_msg = final_msg.replace("Book now", "Reserve your spot")
                final_msg = final_msg.replace("Treat yourself", "Indulge in excellence")
                final_msg = final_msg.replace("Get ", "Receive ")

            # Ensure it's not too long
            words = final_msg.split()
            if len(words) > 30:
                final_msg = " ".join(words[:30]) + "..."

            score = self._score_message(final_msg, trigger, offer)
            
            tags = trig_conf["tags"].copy()
            if "%" in offer or "off" in offer.lower():
                tags.append("discount")
            tags.append(mode["id"])

            # Decision Engine Reasoning format tailored to mode
            inputs = []
            if trigger != "default": inputs.append(trigger)
            if category != "default": inputs.append(category)
            if current_customer != "default": inputs.append(current_customer + " user")
            
            if not inputs: inputs.append("general context")
                
            outcomes = [mode["name"].split(" ")[1] + " strategy"]
            
            if mode["id"] == "aggressive":
                outcomes.append("high urgency")
                outcomes.append("strong discount")
            elif mode["id"] == "premium":
                outcomes.append("brand-focused")
                outcomes.append("less discount emphasis")
            elif mode["id"] == "retention":
                outcomes.append("win-back hook")
                outcomes.append("loyalty trigger")
            elif mode["id"] == "growth":
                outcomes.append("acquisition hook")
                outcomes.append("welcome offer")

            reasoning = f"{' + '.join(inputs)} -> {' + '.join(outcomes)}"

            # Calculate CTR heuristic
            base_ctr = 3.5
            if mode["id"] == "aggressive": base_ctr += 3.0
            if mode["id"] == "growth": base_ctr += 2.0
            if "today" in final_msg.lower() or "now" in final_msg.lower() or "hurry" in final_msg.lower(): base_ctr += 1.5
            if "%" in offer or "off" in offer.lower() or "free" in offer.lower(): base_ctr += 2.0
            if trigger != "default": base_ctr += 1.0
            
            expected_ctr = f"{base_ctr:.1f}%"
            
            # Calculate Conversion heuristic
            if score >= 85: expected_conversion = "High"
            elif score >= 65: expected_conversion = "Medium"
            else: expected_conversion = "Low"

            # Apply learning boost: bump score for historically winning mode
            if boost_mode_id and mode["id"] == boost_mode_id:
                score = min(score + 10, 100)

            variations.append({
                "mode_id": mode["id"],
                "mode_name": mode["name"],
                "message": final_msg,
                "reasoning": reasoning,
                "tags": list(set(tags)),
                "confidence_score": score,
                "expected_ctr": expected_ctr,
                "expected_conversion": expected_conversion
            })

        # Generate A/B Test Recommendation
        sorted_vars = sorted(variations, key=lambda x: x["confidence_score"], reverse=True)
        winner = sorted_vars[0]
        
        ab_test_recommendation = f"Message {winner['mode_name']} should perform best. "
        if winner["mode_id"] == "aggressive":
            ab_test_recommendation += f"The {trigger if trigger != 'default' else 'current'} timing paired with a strong discount creates high urgency, driving immediate clicks."
        elif winner["mode_id"] == "premium":
            ab_test_recommendation += f"By softening the discount and focusing on brand tone, this builds long-term value while still capturing interest."
        elif winner["mode_id"] == "retention":
            ab_test_recommendation += f"Directly addressing the user's absence (win-back hook) outperforms generic urgency for inactive customers."
        elif winner["mode_id"] == "growth":
            ab_test_recommendation += f"New customers respond best to welcoming hooks. The focus on discovery makes this highly clickable."
        else:
            ab_test_recommendation += "The balance of urgency, tone, and offer makes this the most statistically sound option."

        # Generate Merchant Insights
        merchant_insights = {
            "analysis": "General campaign broadcast.",
            "strategy": "Maintain standard promotional messaging.",
            "suggested_discount": "10-15%"
        }
        
        if trigger == "low sales":
            merchant_insights["analysis"] = "Conversion is currently low likely due to off-peak timing or low footfall."
            merchant_insights["strategy"] = "Deploy aggressive urgency hooks to drive immediate action."
            merchant_insights["suggested_discount"] = "25-30%"
        elif trigger == "weekend":
            merchant_insights["analysis"] = "Weekend traffic is inherently higher with increased willingness to spend."
            merchant_insights["strategy"] = "Focus on premium/leisure messaging to maximize margins without steep discounts."
            merchant_insights["suggested_discount"] = "10-15%"
        elif trigger == "payday":
            merchant_insights["analysis"] = "Customers have fresh disposable income and are looking to splurge."
            merchant_insights["strategy"] = "Push premium items and upsell packages."
            merchant_insights["suggested_discount"] = "5-10%"
        elif trigger == "rain":
            merchant_insights["analysis"] = "Weather is suppressing foot traffic but increasing desire for indoor comfort."
            merchant_insights["strategy"] = "Focus on delivery, comfort, and staying cozy."
            merchant_insights["suggested_discount"] = "15-20%"
        elif trigger == "lunch time":
            merchant_insights["analysis"] = "High intent for immediate consumption."
            merchant_insights["strategy"] = "Push fast-moving combos or quick-service items."
            merchant_insights["suggested_discount"] = "10-20%"

        return {
            "merchant_insights": merchant_insights,
            "ab_test_recommendation": ab_test_recommendation,
            "modes": variations
        }

if __name__ == "__main__":
    engine = MessageEngine()
    result = engine.generate(
        category="restaurant",
        merchant_name="Pizza Hut",
        offer="Buy 1 Get 1 Free",
        trigger="weekend",
        customer_type="inactive"
    )
    print(json.dumps(result, indent=2))
