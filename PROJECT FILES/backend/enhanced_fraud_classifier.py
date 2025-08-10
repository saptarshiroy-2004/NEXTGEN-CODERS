import re
import json
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import logging
from pathlib import Path

# For advanced text processing
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.naive_bayes import MultinomialNB
    from sklearn.pipeline import Pipeline
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score, classification_report
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False
    print("⚠️ scikit-learn not installed. Install with: pip install scikit-learn")

try:
    import nltk
    from nltk.corpus import stopwords
    from nltk.stem import PorterStemmer
    from nltk.tokenize import word_tokenize
    HAS_NLTK = True
    
    # Download required NLTK data
    try:
        nltk.data.find('tokenizers/punkt')
        nltk.data.find('corpora/stopwords')
    except LookupError:
        nltk.download('punkt', quiet=True)
        nltk.download('stopwords', quiet=True)
except ImportError:
    HAS_NLTK = False
    print("⚠️ nltk not installed. Install with: pip install nltk")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class FraudPattern:
    """Represents a fraud pattern for detection"""
    pattern: str
    weight: float
    category: str
    description: str
    regex: bool = False

@dataclass
class ClassificationResult:
    """Enhanced classification result with detailed analysis"""
    label: str
    confidence: float
    rationale: str
    keywords: List[str]
    risk_score: float
    fraud_indicators: List[str]
    linguistic_features: Dict[str, float]
    pattern_matches: List[str]
    recommendation: str
    timestamp: str
    detailed_analysis: Dict = None

# Alias for backward compatibility
FraudAnalysisResult = ClassificationResult

class EnhancedFraudClassifier:
    """Enhanced fraud classification with ML and pattern matching"""
    
    def __init__(self, model_path: Optional[str] = None):
        self.fraud_patterns = self._load_fraud_patterns()
        self.stop_words = set(['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'])
        self.stemmer = None
        self.ml_pipeline = None
        
        # Initialize NLTK components if available
        if HAS_NLTK:
            try:
                self.stop_words.update(stopwords.words('english'))
                self.stemmer = PorterStemmer()
                logger.info("✅ NLTK components loaded")
            except Exception as e:
                logger.warning(f"⚠️ NLTK initialization warning: {e}")
        
        # Initialize ML pipeline if sklearn is available
        if HAS_SKLEARN:
            self._initialize_ml_pipeline()
        
        logger.info(f"🛡️ Enhanced Fraud Classifier initialized with {len(self.fraud_patterns)} patterns")
    
    def _load_fraud_patterns(self) -> List[FraudPattern]:
        """Load comprehensive fraud patterns"""
        patterns = [
            # Financial scams
            FraudPattern(r"\b(transfer|send)\s+(money|cash|funds)", 2.0, "financial", "Money transfer request", True),
            FraudPattern(r"\b(bank|account)\s+(details|information|number)", 1.8, "financial", "Bank account information request", True),
            FraudPattern(r"\b(credit\s+card|debit\s+card)\s+(number|details)", 2.2, "financial", "Credit card information request", True),
            FraudPattern(r"\b(social\s+security|ssn)\s+(number)?", 2.5, "identity", "SSN request", True),
            FraudPattern(r"\b(routing\s+number|account\s+number)", 2.0, "financial", "Banking details request", True),
            
            # Verification scams
            FraudPattern(r"\b(verify|confirm)\s+(your|account|identity)", 1.5, "verification", "Identity verification request", True),
            FraudPattern(r"\b(otp|one\s+time\s+password|verification\s+code)", 2.1, "verification", "OTP/verification code request", True),
            FraudPattern(r"\b(enter|provide|give)\s+(code|password|pin)", 1.9, "verification", "Security code request", True),
            FraudPattern(r"\b(two\s+factor|2fa|multi\s+factor)\s+authentication", 1.7, "verification", "2FA bypass attempt", True),
            
            # Urgency tactics
            FraudPattern(r"\b(urgent|emergency|immediate|expires?\s+(today|soon))", 1.3, "urgency", "Urgency pressure tactic", True),
            FraudPattern(r"\b(act\s+now|limited\s+time|hurry|quickly)", 1.2, "urgency", "Time pressure tactic", True),
            FraudPattern(r"\b(suspended|frozen|blocked|closed)\s+(account|card)", 1.6, "urgency", "Account threat", True),
            
            # Authority impersonation
            FraudPattern(r"\b(irs|internal\s+revenue|tax\s+department)", 2.0, "impersonation", "IRS impersonation", True),
            FraudPattern(r"\b(fbi|police|law\s+enforcement|detective)", 2.2, "impersonation", "Law enforcement impersonation", True),
            FraudPattern(r"\b(microsoft|apple|google|amazon)\s+(support|security)", 1.8, "impersonation", "Tech company impersonation", True),
            FraudPattern(r"\b(bank|financial\s+institution)\s+(representative|agent)", 1.7, "impersonation", "Bank impersonation", True),
            
            # Tech support scams
            FraudPattern(r"\b(virus|malware|infected|hacked)\s+(computer|device)", 1.9, "tech_scam", "Fake virus/malware alert", True),
            FraudPattern(r"\b(remote\s+access|team\s+viewer|screen\s+share)", 2.3, "tech_scam", "Remote access request", True),
            FraudPattern(r"\b(windows\s+key|run\s+command|cmd|registry)", 2.0, "tech_scam", "System access instruction", True),
            
            # Prize/lottery scams
            FraudPattern(r"\b(congratulations|winner|won|lottery|prize)", 1.4, "prize_scam", "Prize/lottery scam", True),
            FraudPattern(r"\b(claim|collect)\s+(prize|winnings|money)", 1.6, "prize_scam", "Prize claim request", True),
            
            # Romance/relationship scams
            FraudPattern(r"\b(love|relationship|marry|marriage)\s+.*(money|help|emergency)", 1.8, "romance", "Romance scam indicator", True),
            FraudPattern(r"\b(deployed|military|overseas)\s+.*(money|funds|help)", 1.9, "romance", "Military romance scam", True),
            
            # Investment scams
            FraudPattern(r"\b(investment|crypto|bitcoin|trading)\s+(opportunity|guaranteed)", 1.7, "investment", "Investment scam", True),
            FraudPattern(r"\b(high\s+returns|guaranteed\s+profit|double\s+your\s+money)", 2.0, "investment", "Unrealistic returns promise", True),
            
            # Charity scams
            FraudPattern(r"\b(donation|charity|disaster\s+relief)\s+.*(urgent|help|emergency)", 1.5, "charity", "Charity scam", True),
            
            # Simple keyword patterns (backward compatibility)
            FraudPattern("transfer", 1.2, "financial", "Money transfer keyword", False),
            FraudPattern("bank", 1.0, "financial", "Banking keyword", False),
            FraudPattern("account", 1.0, "financial", "Account keyword", False),
            FraudPattern("otp", 1.8, "verification", "OTP keyword", False),
            FraudPattern("code", 1.1, "verification", "Code keyword", False),
            FraudPattern("verify", 1.3, "verification", "Verification keyword", False),
            FraudPattern("password", 1.5, "security", "Password keyword", False),
            FraudPattern("ssn", 2.0, "identity", "SSN keyword", False),
            FraudPattern("social security", 2.2, "identity", "Social Security keyword", False),
            FraudPattern("urgent", 1.2, "urgency", "Urgency keyword", False),
            FraudPattern("immediate", 1.3, "urgency", "Immediate action keyword", False),
            FraudPattern("suspended", 1.4, "threat", "Account suspension threat", False),
            FraudPattern("frozen", 1.4, "threat", "Account frozen threat", False),
        ]
        
        return patterns
    
    def _initialize_ml_pipeline(self):
        """Initialize machine learning pipeline with training data"""
        try:
            # Generate synthetic training data for demonstration
            # In production, use real labeled dataset
            training_data = self._generate_training_data()
            
            if training_data:
                texts, labels = zip(*training_data)
                
                # Create ML pipeline
                self.ml_pipeline = Pipeline([
                    ('tfidf', TfidfVectorizer(max_features=1000, stop_words='english', ngram_range=(1, 2))),
                    ('classifier', MultinomialNB(alpha=0.1))
                ])
                
                # Train the pipeline
                self.ml_pipeline.fit(texts, labels)
                
                # Test accuracy with cross-validation
                X_train, X_test, y_train, y_test = train_test_split(texts, labels, test_size=0.2, random_state=42)
                self.ml_pipeline.fit(X_train, y_train)
                predictions = self.ml_pipeline.predict(X_test)
                accuracy = accuracy_score(y_test, predictions)
                
                logger.info(f"✅ ML Pipeline trained with {accuracy:.2%} accuracy")
            
        except Exception as e:
            logger.error(f"❌ ML pipeline initialization failed: {e}")
            self.ml_pipeline = None
    
    def _generate_training_data(self) -> List[Tuple[str, str]]:
        """Generate synthetic training data for ML model"""
        # In a real application, this would be replaced with a proper labeled dataset
        scam_texts = [
            "Hello, this is calling from your bank. Your account has been suspended due to suspicious activity. Please verify your account by providing your social security number and account details.",
            "Congratulations! You have won $1,000,000 in our lottery. To claim your prize, please send $500 for processing fees and provide your bank account information.",
            "This is Microsoft Technical Support. Your computer is infected with a virus. Please allow us remote access to fix the problem immediately.",
            "Your credit card has been frozen due to fraudulent activity. Please call this number and provide your card details to unfreeze it urgently.",
            "IRS here. You owe $5,000 in back taxes. Pay immediately or face arrest. Provide your bank details for payment.",
            "Hi dear, I'm deployed overseas and need emergency funds. Please send money via wire transfer. I love you.",
            "Invest in our cryptocurrency scheme and double your money in 30 days. Guaranteed returns of 200%.",
            "Your Amazon account has been hacked. Please verify your identity by providing your password and OTP code.",
            "Police department calling. There's a warrant for your arrest. Pay fine immediately using gift cards.",
            "Bank of America security. Someone is trying to access your account. Enter your PIN to verify identity."
        ]
        
        safe_texts = [
            "Hello, this is John from ABC Company. I wanted to follow up on your recent purchase and see if you have any questions.",
            "Hi, this is Sarah calling to remind you about your doctor's appointment tomorrow at 2 PM.",
            "Good morning, this is the school nurse. Your child has a mild fever and should be picked up.",
            "This is Pizza Palace confirming your delivery order for tonight at 7 PM.",
            "Hello, this is the car dealership. Your vehicle service is complete and ready for pickup.",
            "Hi, this is your local library. The book you reserved is now available for pickup.",
            "This is Dr. Smith's office calling to confirm your appointment next week.",
            "Hello, this is the utility company. We're calling to inform you about planned maintenance in your area.",
            "Hi, this is the customer service team following up on your recent inquiry about our product warranty.",
            "This is the hotel confirming your reservation for next weekend. Looking forward to your stay."
        ]
        
        suspicious_texts = [
            "This is your bank calling about unusual activity on your account. Can you confirm if you made a large purchase yesterday?",
            "Hi, this is regarding your insurance policy. There might be an issue with your recent claim.",
            "Hello, we're calling about your credit report. There seems to be some errors that need correction.",
            "This is about your recent online order. There was a payment processing issue.",
            "Hi, calling from customer support. We need to update your account information.",
            "This is regarding your subscription service. Your payment method needs to be updated.",
            "Hello, we're calling about your recent application. We need additional verification.",
            "Hi, this is about your utility bill. There seems to be an outstanding balance.",
            "This is regarding your recent transaction. We need to verify some details.",
            "Hello, calling about your account status. There might be some security concerns."
        ]
        
        training_data = []
        training_data.extend([(text, 'Scam') for text in scam_texts])
        training_data.extend([(text, 'Safe') for text in safe_texts])
        training_data.extend([(text, 'Suspicious') for text in suspicious_texts])
        
        return training_data
    
    def preprocess_text(self, text: str) -> str:
        """Preprocess text for analysis"""
        # Convert to lowercase
        text = text.lower()
        
        # Remove special characters but keep spaces
        text = re.sub(r'[^a-zA-Z0-9\s]', ' ', text)
        
        # Remove extra whitespaces
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Tokenize and remove stopwords if NLTK is available
        if HAS_NLTK and self.stemmer:
            try:
                tokens = word_tokenize(text)
                tokens = [self.stemmer.stem(token) for token in tokens if token not in self.stop_words]
                text = ' '.join(tokens)
            except:
                pass  # Fallback to simple preprocessing
        
        return text
    
    def extract_linguistic_features(self, text: str) -> Dict[str, float]:
        """Extract linguistic features for analysis"""
        words = text.split()
        sentences = text.split('.')
        
        features = {
            'word_count': len(words),
            'sentence_count': len([s for s in sentences if s.strip()]),
            'avg_word_length': np.mean([len(word) for word in words]) if words else 0,
            'exclamation_count': text.count('!'),
            'question_count': text.count('?'),
            'uppercase_ratio': sum(1 for c in text if c.isupper()) / len(text) if text else 0,
            'digit_count': sum(1 for c in text if c.isdigit()),
            'urgency_words': sum(1 for word in words if word.lower() in ['urgent', 'emergency', 'immediately', 'now', 'quickly', 'hurry']),
            'money_words': sum(1 for word in words if word.lower() in ['money', 'cash', 'dollar', 'payment', 'transfer', 'send', 'pay']),
            'personal_info_words': sum(1 for word in words if word.lower() in ['ssn', 'social', 'security', 'password', 'pin', 'account', 'number']),
        }
        
        return features
    
    def match_fraud_patterns(self, text: str) -> Tuple[List[str], float]:
        """Match text against fraud patterns and calculate risk score"""
        matches = []
        total_weight = 0.0
        text_lower = text.lower()
        
        for pattern in self.fraud_patterns:
            if pattern.regex:
                # Use regex matching
                if re.search(pattern.pattern, text_lower):
                    matches.append(f"{pattern.category}: {pattern.description}")
                    total_weight += pattern.weight
            else:
                # Simple substring matching
                if pattern.pattern.lower() in text_lower:
                    matches.append(f"{pattern.category}: {pattern.description}")
                    total_weight += pattern.weight
        
        return matches, total_weight
    
    def calculate_risk_score(self, text: str, linguistic_features: Dict[str, float], pattern_weight: float) -> float:
        """Calculate overall risk score based on multiple factors"""
        base_score = 0.0
        
        # Pattern matching score (0-0.4)
        pattern_score = min(0.4, pattern_weight / 10.0)
        
        # Linguistic feature score (0-0.3)
        linguistic_score = 0.0
        if linguistic_features['urgency_words'] > 0:
            linguistic_score += 0.05
        if linguistic_features['money_words'] > 0:
            linguistic_score += 0.1
        if linguistic_features['personal_info_words'] > 0:
            linguistic_score += 0.15
        if linguistic_features['exclamation_count'] > 2:
            linguistic_score += 0.05
        if linguistic_features['uppercase_ratio'] > 0.3:
            linguistic_score += 0.05
        
        linguistic_score = min(0.3, linguistic_score)
        
        # ML prediction score (0-0.3) if available
        ml_score = 0.0
        if self.ml_pipeline:
            try:
                prediction_proba = self.ml_pipeline.predict_proba([text])[0]
                classes = self.ml_pipeline.classes_
                if 'Scam' in classes:
                    scam_idx = list(classes).index('Scam')
                    ml_score = prediction_proba[scam_idx] * 0.3
            except Exception as e:
                logger.debug(f"ML prediction error: {e}")
        
        total_score = pattern_score + linguistic_score + ml_score
        return min(1.0, total_score)
    
    def generate_recommendation(self, risk_score: float, label: str, matches: List[str]) -> str:
        """Generate actionable recommendations based on classification"""
        if label == "Scam" or risk_score > 0.7:
            return ("⚠️ HIGH RISK: This appears to be a scam call. Do NOT provide personal information, "
                   "money, or access to your devices. Hang up immediately and report the call.")
        elif label == "Suspicious" or risk_score > 0.4:
            return ("⚠️ SUSPICIOUS: This call shows warning signs. Be cautious, verify the caller's "
                   "identity independently, and avoid sharing sensitive information.")
        else:
            return ("✅ SAFE: This call appears legitimate, but always verify caller identity "
                   "for sensitive requests.")
    
    def classify(self, transcript: str) -> ClassificationResult:
        """Enhanced classification with detailed analysis"""
        try:
            # Preprocess text
            processed_text = self.preprocess_text(transcript)
            
            # Extract features
            linguistic_features = self.extract_linguistic_features(transcript)
            
            # Match fraud patterns
            matches, pattern_weight = self.match_fraud_patterns(transcript)
            
            # Calculate risk score
            risk_score = self.calculate_risk_score(processed_text, linguistic_features, pattern_weight)
            
            # Determine label and confidence
            if risk_score > 0.7:
                label = "Scam"
                confidence = min(0.95, 0.7 + (risk_score - 0.7) * 0.5)
            elif risk_score > 0.4:
                label = "Suspicious"
                confidence = 0.6 + (risk_score - 0.4) * 0.3
            else:
                label = "Safe"
                confidence = max(0.3, 1.0 - risk_score)
            
            # Use ML prediction if available and more confident
            if self.ml_pipeline:
                try:
                    ml_prediction = self.ml_pipeline.predict([processed_text])[0]
                    ml_proba = self.ml_pipeline.predict_proba([processed_text])[0].max()
                    
                    # Use ML prediction if it's more confident
                    if ml_proba > confidence:
                        label = ml_prediction
                        confidence = min(0.95, ml_proba)
                        
                except Exception as e:
                    logger.debug(f"ML classification error: {e}")
            
            # Extract keywords from matches
            keywords = []
            for match in matches:
                # Extract the description part
                if ": " in match:
                    keywords.append(match.split(": ")[1])
            
            # Generate rationale
            if matches:
                rationale = f"Detected {len(matches)} fraud indicators: {', '.join(matches[:3])}"
                if len(matches) > 3:
                    rationale += f" and {len(matches) - 3} more."
            else:
                rationale = "No significant fraud indicators detected."
            
            # Generate recommendation
            recommendation = self.generate_recommendation(risk_score, label, matches)
            
            return ClassificationResult(
                label=label,
                confidence=round(confidence, 3),
                rationale=rationale,
                keywords=keywords,
                risk_score=round(risk_score, 3),
                fraud_indicators=matches,
                linguistic_features=linguistic_features,
                pattern_matches=[match.split(": ")[0] for match in matches],
                recommendation=recommendation,
                timestamp=datetime.utcnow().isoformat()
            )
            
        except Exception as e:
            logger.error(f"Classification error: {e}")
            # Return fallback classification
            return ClassificationResult(
                label="Safe",
                confidence=0.3,
                rationale=f"Classification error: {str(e)}",
                keywords=[],
                risk_score=0.0,
                fraud_indicators=[],
                linguistic_features={},
                pattern_matches=[],
                recommendation="Unable to analyze call. Please use caution.",
                timestamp=datetime.utcnow().isoformat()
            )
    
    def classify_dict(self, transcript: str) -> Dict:
        """Return classification as dictionary (backward compatibility)"""
        result = self.classify(transcript)
        return {
            "label": result.label,
            "confidence": result.confidence,
            "rationale": result.rationale,
            "keywords": result.keywords,
            "risk_score": result.risk_score,
            "recommendation": result.recommendation
        }

# Enhanced offline classification function (backward compatibility)
def enhanced_offline_classify(transcript: str) -> Dict:
    """Enhanced offline classification with improved accuracy"""
    classifier = EnhancedFraudClassifier()
    return classifier.classify_dict(transcript)

# Global classifier instance for performance
_global_classifier = None

def get_global_classifier() -> EnhancedFraudClassifier:
    """Get or create global classifier instance"""
    global _global_classifier
    if _global_classifier is None:
        _global_classifier = EnhancedFraudClassifier()
    return _global_classifier
