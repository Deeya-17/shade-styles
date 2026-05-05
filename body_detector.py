# pages/body_detector.py

class BodyDetector:
    def __init__(self):
        pass

    def classify_by_measurements(self, bust, waist, hips):
        """Classify body shape based on measurements"""
        if bust <= 0 or waist <= 0 or hips <= 0:
            return "Unknown", 0.0

        avg = (bust + hips) / 2.0
        rel_diff = abs(bust - hips) / avg
        waist_to_bust = waist / bust
        waist_to_hips = waist / hips
        bust_minus_hips = bust - hips
        hips_minus_bust = hips - bust

        balanced_threshold = 0.05
        significant_threshold = 0.05

        if rel_diff <= balanced_threshold:
            if waist_to_bust <= 0.75:
                shape = "Hourglass"
                confidence = max(0.7, 1.0 - rel_diff)
            elif waist_to_bust >= 0.80:
                shape = "Apple"
                confidence = 0.7
            else:
                shape = "Rectangle"
                confidence = 0.6
        else:
            if hips_minus_bust / avg >= significant_threshold:
                shape = "Pear"
                confidence = min(0.95, 0.5 + (hips_minus_bust / avg))
            elif bust_minus_hips / avg >= significant_threshold:
                shape = "Inverted Triangle"
                confidence = min(0.95, 0.5 + (bust_minus_hips / avg))
            else:
                shape = "Rectangle"
                confidence = 0.5

        confidence = max(0.0, min(1.0, confidence))
        return shape, round(confidence, 2)

    def get_attire_recommendations(self, shape):
        recommendations = {
            "Hourglass": [
                "Wrap dresses to highlight waist",
                "Fitted tops and high-waist bottoms",
                "Belts to accentuate curves",
                "V-necklines to elongate neck",
                "Jumpsuits",
                "Tailored jackets"
            ],
            "Apple": [
                "Empire waist dresses",
                "A-line skirts",
                "V-neck and scoop neck tops",
                "Flowy tops over fitted pants",
                "Structured jackets to define shoulders",
                "Trench coats"
            ],
            "Pear": [
                "Maxi Dresses",
                "A-line and flared skirts",
                "Off-shoulder and embellished tops",
                "Dark bottoms with bright tops",
                "High-waist pants to elongate legs",
                "Tailored jackets ending above hips"
            ],
            "Rectangle": [
                "Layered outfits to create curves",
                "Peplum tops and dresses",
                "Belts to define waist",
                "Waist-length shirts",
                "Ruffled or patterned tops",
                "Bodycon or fit-and-flare dresses"

            ],
            "Inverted Triangle": [
                "V-necklines to reduce shoulder width",
                "A-line skirts and wide-leg pants",
                "Darker tops with lighter bottoms",
                "Flowy skirts to balance proportions",
                "Minimal shoulder embellishments",
                "Strapless dresses"
            ],
            "Unknown": [
                "General fitted clothing",
                "Comfortable casual wear",
                "Neutral colors"
            ]
        }
        return recommendations.get(shape, [])

    def run_analysis(self, bust=36, waist=28, hips=38):
        """Main entrypoint used by Flask"""
        shape, conf = self.classify_by_measurements(bust, waist, hips)
        attire_list = self.get_attire_recommendations(shape)
        return {
            "shape": shape,
            "confidence": conf,
            "bust": bust,
            "waist": waist,
            "hips": hips,
            "attire": attire_list
        }
