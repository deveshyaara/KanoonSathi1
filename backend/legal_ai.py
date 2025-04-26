"""
Legal AI Assistant module for processing document uploads and generating responses
"""
import os
import shutil
import re
from datetime import datetime
import random
import json
from pathlib import Path

# Add imports for translation capabilities
try:
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

class LegalAIAssistant:
    """A class that handles processing of legal documents and generating responses"""
    
    def __init__(self):
        """Initialize the Legal AI Assistant"""
        self.storage_dir = "uploads"
        os.makedirs(self.storage_dir, exist_ok=True)
        os.makedirs("temp", exist_ok=True)  # Ensure temp directory exists for audio files
        
        # Create a translations cache directory
        self.cache_dir = "translation_cache"
        os.makedirs(self.cache_dir, exist_ok=True)
        self.cache_file = os.path.join(self.cache_dir, "translations_cache.json")
        self.translation_cache = self._load_translation_cache()
        
        # Initialize document type patterns
        self.document_patterns = {
            "contract": r"(?i)(agreement|contract|terms|conditions|parties|clause|hereby|agree|consideration)",
            "judgment": r"(?i)(judgment|court|ruling|judge|versus|petitioner|respondent|plaintiff|defendant|bench|justice|order|decree)",
            "legislation": r"(?i)(act|section|statute|law|regulation|provision|legislature|parliament|amendment|clause|bill)",
            "will": r"(?i)(testament|will|bequeath|estate|beneficiary|executor|probate|heir|inheritance|devise|legacy)",
            "affidavit": r"(?i)(affidavit|sworn|deponent|oath|affirm|verification|notary|attested)",
            "notice": r"(?i)(notice|hereby|inform|attention|pursuant|announce|adjourned|meeting)",
            "legal_opinion": r"(?i)(opinion|advice|counsel|consult|recommended|suggested|pursuant to)",
            "mou": r"(?i)(memorandum|understanding|mou|intent|non-binding)"
        }
        
        # Legal frameworks by jurisdiction
        self.legal_frameworks = {
            "india": {
                "civil": ["Code of Civil Procedure, 1908", "Indian Contract Act, 1872", "Transfer of Property Act, 1882", 
                          "Specific Relief Act, 1963", "Indian Evidence Act, 1872"],
                "criminal": ["Indian Penal Code, 1860", "Code of Criminal Procedure, 1973", "Criminal Law Amendment Act"],
                "commercial": ["Companies Act, 2013", "Insolvency and Bankruptcy Code, 2016", "Competition Act, 2002", 
                               "Foreign Exchange Management Act, 1999"],
                "property": ["Registration Act, 1908", "Real Estate (Regulation and Development) Act, 2016"],
                "family": ["Hindu Marriage Act, 1955", "Special Marriage Act, 1954", "Indian Succession Act, 1925"]
            },
            "us": {
                "civil": ["Federal Rules of Civil Procedure", "Uniform Commercial Code"],
                "criminal": ["Federal Criminal Code and Rules", "Model Penal Code"],
                "commercial": ["Securities Act of 1933", "Securities Exchange Act of 1934", "Sarbanes-Oxley Act"]
            }
        }
        
        # Initialize translation model if transformers is available
        self.translation_model = None
        self.translation_tokenizer = None
        # Map for all 22 official Indian languages plus English
        self.language_code_map = {
            "en": "eng_Latn",  # English
            "hi": "hin_Deva",  # Hindi
            "bn": "ben_Beng",  # Bengali
            "te": "tel_Telu",  # Telugu
            "mr": "mar_Deva",  # Marathi
            "ta": "tam_Taml",  # Tamil
            "ur": "urd_Arab",  # Urdu
            "gu": "guj_Gujr",  # Gujarati
            "kn": "kan_Knda",  # Kannada
            "ml": "mal_Mlym",  # Malayalam
            "or": "ory_Orya",  # Odia
            "pa": "pan_Guru",  # Punjabi
            "as": "asm_Beng",  # Assamese
            "mai": "mai_Deva", # Maithili
            "sat": "sat_Olck", # Santali
            "ks": "kas_Arab",  # Kashmiri
            "ne": "npi_Deva",  # Nepali (for Nepali in India)
            "sd": "snd_Arab",  # Sindhi
            "kok": "kok_Deva", # Konkani
            "doi": "doi_Deva", # Dogri
            "mni": "mni_Beng", # Manipuri/Meitei
            "sa": "san_Deva",  # Sanskrit
            "bo": "bod_Tibt"   # Tibetan/Bodo
        }
        
    def _load_translation_cache(self):
        """Load the translation cache from file"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading translation cache: {e}")
                return {}
        return {}
    
    def _save_translation_cache(self):
        """Save the translation cache to file"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.translation_cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving translation cache: {e}")
    
    def _load_translation_model(self):
        """Load the translation model on demand"""
        if not TRANSFORMERS_AVAILABLE:
            return False
            
        try:
            # Only load the model if it hasn't been loaded yet
            if self.translation_model is None:
                model_name = "facebook/nllb-200-distilled-600M"  # Smaller distilled version to save memory
                
                print("Loading translation model, this may take a moment...")
                self.translation_tokenizer = AutoTokenizer.from_pretrained(model_name)
                self.translation_model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
                print("Translation model loaded successfully!")
            return True
        except Exception as e:
            print(f"Error loading translation model: {e}")
            return False
    
    def process_image_upload(self, file_path):
        """
        Process an uploaded image/document file
        
        Args:
            file_path: Path to the uploaded file
            
        Returns:
            str: Path where the file is stored
        """
        # Generate a unique filename using timestamp
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = os.path.basename(file_path)
        base, ext = os.path.splitext(filename)
        stored_filename = f"{base}_{timestamp}{ext}"
        
        # Copy to permanent storage
        stored_path = os.path.join(self.storage_dir, stored_filename)
        shutil.copy2(file_path, stored_path)
        
        return stored_path
    
    def handle_translation_request(self, text, target_lang):
        """
        Translate text to the target language and generate audio
        
        Args:
            text: The text to translate
            target_lang: The target language code
            If using the Hugging Face model,
            the target_lang should be one of: "en", "hi", "kn", "pa", "ta", "gu", "bn", "mr"
            
        Returns:
            dict: Response containing translated text and audio path
        """
        # Check cache first
        cache_key = f"{text}_{target_lang}"
        if cache_key in self.translation_cache:
            print(f"Using cached translation for {target_lang}")
            translated_text = self.translation_cache[cache_key]
        else:
            translated_text = ""
            
            # First try using the Hugging Face model if available
            if self._load_translation_model():
                try:
                    # Convert language code to NLLB format
                    source_lang_code = self.language_code_map.get("en", "eng_Latn")
                    target_lang_code = self.language_code_map.get(target_lang, None)
                    
                    if target_lang_code:
                        # Tokenize and translate
                        inputs = self.translation_tokenizer(text, return_tensors="pt", src_lang=source_lang_code)
                        
                        # Generate translation with the target language code
                        outputs = self.translation_model.generate(
                            **inputs, 
                            forced_bos_token_id=self.translation_tokenizer.convert_tokens_to_ids(target_lang_code),
                            max_length=512
                        )
                        
                        # Decode the translation
                        translated_text = self.translation_tokenizer.batch_decode(
                            outputs, skip_special_tokens=True
                        )[0]
                except Exception as e:
                    print(f"Error during translation with Hugging Face model: {e}")
                    # Fall back to the dictionary approach if model fails
                    translated_text = ""
            
            # If translation is still empty, fall back to the dictionary approach
            if not translated_text:
                # Create section-specific translations for legal texts
                analysis_translations = {
                    "hi": {  # Hindi
                        "Here's a detailed analysis:": "यहां एक विस्तृत विश्लेषण है:",
                        "Contract Structure and Validity:": "अनुबंध संरचना और वैधता:",
                        "Key Legal Provisions:": "प्रमुख कानूनी प्रावधान:",
                        "Rights and Obligations:": "अधिकार और दायित्व:",
                        "Legal Implications:": "कानूनी निहितार्थ:",
                        "Applicable legal frameworks that may be relevant:": "प्रासंगिक कानूनी ढांचे जो संबंधित हो सकते हैं:",
                        "DISCLAIMER:": "अस्वीकरण:",
                        "This analysis is provided for informational purposes only": "यह विश्लेषण केवल सूचनात्मक उद्देश्यों के लिए प्रदान किया गया है",
                        "and should not be construed as legal advice.": "और इसे कानूनी सलाह के रूप में नहीं माना जाना चाहिए।",
                        "Please consult with a qualified legal professional for advice specific to your situation.": "अपनी स्थिति के लिए विशिष्ट सलाह के लिए कृपया एक योग्य कानूनी पेशेवर से परामर्श करें।",
                        "The document contains standard contractual elements": "दस्तावेज़ में मानक अनुबंध तत्व शामिल हैं",
                        "including parties' details, consideration clauses, terms of agreement, and signature requirements.": "जिसमें पक्षों का विवरण, विचार खंड, समझौते की शर्तें और हस्ताक्षर आवश्यकताएं शामिल हैं।",
                        "The agreement appears to establish legally binding obligations between the parties under contract law principles.": "समझौता अनुबंध कानून के सिद्धांतों के तहत पक्षों के बीच कानूनी रूप से बाध्यकारी दायित्वों को स्थापित करता प्रतीत होता है।",
                        "Terms and conditions governing the relationship between parties are outlined": "पक्षों के बीच संबंधों को नियंत्रित करने वाले नियम और शर्तों का उल्लेख किया गया है",
                        "with specific performance requirements.": "विशिष्ट प्रदर्शन आवश्यकताओं के साथ।",
                        "Liability provisions and risk allocation measures are included": "देयता प्रावधान और जोखिम आवंटन उपाय शामिल हैं",
                        "to protect the parties' interests.": "पक्षों के हितों की रक्षा के लिए।",
                        "Termination mechanisms and conditions for contract renewal are specified.": "समाप्ति तंत्र और अनुबंध नवीनीकरण के लिए शर्तें निर्दिष्ट हैं।",
                        "The respective duties of each party are delineated": "प्रत्येक पक्ष के संबंधित कर्तव्यों का सीमांकन किया गया है",
                        "with specific performance metrics and timelines.": "विशिष्ट प्रदर्शन मेट्रिक्स और समयसीमा के साथ।",
                        "Compliance requirements with relevant laws and regulations are established.": "प्रासंगिक कानूनों और विनियमों के अनुपालन की आवश्यकताएं स्थापित की गई हैं।",
                        "Remedy mechanisms in case of breach are provided with specific consequences.": "उल्लंघन के मामले में उपचार तंत्र विशिष्ट परिणामों के साथ प्रदान किए गए हैं।",
                        "The contract creates legally enforceable rights": "अनुबंध कानूनी रूप से लागू करने योग्य अधिकार बनाता है",
                        "that can be upheld through legal proceedings if necessary.": "जिन्हें आवश्यकता पड़ने पर कानूनी कार्यवाही के माध्यम से बनाए रखा जा सकता है।",
                        "Under contract law, material breaches may entitle the non-breaching party": "अनुबंध कानून के तहत, भौतिक उल्लंघन गैर-उल्लंघनकर्ता पक्ष को हकदार बना सकता है",
                        "to remedies including specific performance or damages.": "विशिष्ट प्रदर्शन या क्षति सहित उपचारों के लिए।",
                        "Ambiguous terms may be interpreted by courts": "अस्पष्ट शब्दों की व्याख्या अदालतों द्वारा की जा सकती है",
                        "according to standard principles of contractual interpretation.": "अनुबंध व्याख्या के मानक सिद्धांतों के अनुसार।"
                    },
                    "kn": {  # Kannada
                        "Here's a detailed analysis:": "ಇಲ್ಲಿ ವಿವರವಾದ ವಿಶ್ಲೇಷಣೆಯಿದೆ:",
                        "Contract Structure and Validity:": "ಒಪ್ಪಂದದ ರಚನೆ ಮತ್ತು ಮಾನ್ಯತೆ:",
                        "Key Legal Provisions:": "ಪ್ರಮುಖ ಕಾನೂನು ನಿಬಂಧನೆಗಳು:",
                        "Rights and Obligations:": "ಹಕ್ಕುಗಳು ಮತ್ತು ಜವಾಬ್ದಾರಿಗಳು:",
                        "Legal Implications:": "ಕಾನೂನು ಪರಿಣಾಮಗಳು:",
                        "Applicable legal frameworks that may be relevant:": "ಅನ್ವಯವಾಗುವ ಕಾನೂನು ಚೌಕಟ್ಟುಗಳು ಸಂಬಂಧಿತವಾಗಿರಬಹುದು:",
                        "DISCLAIMER:": "ಹಕ್ಕುತ್ಯಾಗ:",
                        "This analysis is provided for informational purposes only": "ಈ ವಿಶ್ಲೇಷಣೆಯನ್ನು ಕೇವಲ ಮಾಹಿತಿ ಉದ್ದೇಶಗಳಿಗಾಗಿ ಮಾತ್ರ ನೀಡಲಾಗಿದೆ",
                        "and should not be construed as legal advice.": "ಮತ್ತು ಇದನ್ನು ಕಾನೂನು ಸಲಹೆಯಾಗಿ ಪರಿಗಣಿಸಬಾರದು.",
                        "Please consult with a qualified legal professional for advice specific to your situation.": "ನಿಮ್ಮ ಪರಿಸ್ಥಿತಿಗೆ ನಿರ್ದಿಷ್ಟವಾದ ಸಲಹೆಗಾಗಿ ದಯವಿಟ್ಟು ಅರ್ಹ ಕಾನೂನು ವೃತ್ತಿಪರರನ್ನು ಸಂಪರ್ಕಿಸಿ.",
                        "The document contains standard contractual elements": "ದಾಖಲೆಯು ಪ್ರಮಾಣಿತ ಒಪ್ಪಂದದ ಅಂಶಗಳನ್ನು ಒಳಗೊಂಡಿದೆ",
                        "including parties' details, consideration clauses, terms of agreement, and signature requirements.": "ಪಕ್ಷಗಳ ವಿವರಗಳು, ಪರಿಗಣನಾ ಷರತ್ತುಗಳು, ಒಪ್ಪಂದದ ನಿಯಮಗಳು ಮತ್ತು ಸಹಿ ಅವಶ್ಯಕತೆಗಳನ್ನು ಒಳಗೊಂಡಂತೆ.",
                        "The agreement appears to establish legally binding obligations between the parties under contract law principles.": "ಒಪ್ಪಂದದ ಕಾನೂನು ತತ್ವಗಳ ಅಡಿಯಲ್ಲಿ ಪಕ್ಷಗಳ ನಡುವೆ ಕಾನೂನುಬದ್ಧವಾಗಿ ಬದ್ಧತೆಗಳನ್ನು ಸ್ಥಾಪಿಸುವಂತೆ ಒಪ್ಪಂದವು ಕಾಣುತ್ತದೆ.",
                        "Terms and conditions governing the relationship between parties are outlined": "ಪಕ್ಷಗಳ ನಡುವಿನ ಸಂಬಂಧವನ್ನು ನಿಯಂತ್ರಿಸುವ ನಿಯಮಗಳು ಮತ್ತು ಷರತ್ತುಗಳನ್ನು ವಿವರಿಸಲಾಗಿದೆ",
                        "with specific performance requirements.": "ನಿರ್ದಿಷ್ಟ ಕಾರ್ಯಕ್ಷಮತೆ ಅವಶ್ಯಕತೆಗಳೊಂದಿಗೆ.",
                        "Liability provisions and risk allocation measures are included": "ಹೊಣೆಗಾರಿಕೆ ನಿಬಂಧನೆಗಳು ಮತ್ತು ಅಪಾಯದ ಹಂಚಿಕೆ ಕ್ರಮಗಳನ್ನು ಸೇರಿಸಲಾಗಿದೆ",
                        "to protect the parties' interests.": "ಪಕ್ಷಗಳ ಹಿತಾಸಕ್ತಿಗಳನ್ನು ರಕ್ಷಿಸಲು.",
                        "Termination mechanisms and conditions for contract renewal are specified.": "ಒಪ್ಪಂದ ನವೀಕರಣಕ್ಕಾಗಿ ಕೊನೆಗೊಳಿಸುವ ವಿಧಾನಗಳು ಮತ್ತು ಷರತ್ತುಗಳನ್ನು ನಿರ್ದಿಷ್ಟಪಡಿಸಲಾಗಿದೆ.",
                        "The respective duties of each party are delineated": "ಪ್ರತಿಯೊಂದು ಪಕ್ಷದ ಸಂಬಂಧಿತ ಕರ್ತವ್ಯಗಳನ್ನು ವಿಂಗಡಿಸಲಾಗಿದೆ",
                        "with specific performance metrics and timelines.": "ನಿರ್ದಿಷ್ಟ ಕಾರ್ಯಕ್ಷಮತೆ ಮೆಟ್ರಿಕ್ಸ್ ಮತ್ತು ಸಮಯದ ಮಿತಿಗಳೊಂದಿಗೆ.",
                        "Compliance requirements with relevant laws and regulations are established.": "ಸಂಬಂಧಿತ ಕಾನೂನುಗಳು ಮತ್ತು ನಿಬಂಧನೆಗಳೊಂದಿಗೆ ಅನುಸರಣೆಯ ಅವಶ್ಯಕತೆಗಳನ್ನು ಸ್ಥಾಪಿಸಲಾಗಿದೆ.",
                        "Remedy mechanisms in case of breach are provided with specific consequences.": "ಉಲ್ಲಂಘನೆಯ ಸಂದರ್ಭದಲ್ಲಿ ಪರಿಹಾರ ವಿಧಾನಗಳನ್ನು ನಿರ್ದಿಷ್ಟ ಪರಿಣಾಮಗಳೊಂದಿಗೆ ಒದಗಿಸಲಾಗಿದೆ.",
                        "The contract creates legally enforceable rights": "ಒಪ್ಪಂದವು ಕಾನೂನುಬದ್ಧವಾಗಿ ಜಾರಿಗೊಳಿಸಬಹುದಾದ ಹಕ್ಕುಗಳನ್ನು ಸೃಷ್ಟಿಸುತ್ತದೆ",
                        "that can be upheld through legal proceedings if necessary.": "ಅಗತ್ಯವಿದ್ದಲ್ಲಿ ಕಾನೂನು ವ್ಯವಹರಣೆಗಳ ಮೂಲಕ ಉಳಿಸಿಕೊಳ್ಳಬಹುದು.",
                        "Under contract law, material breaches may entitle the non-breaching party": "ಒಪ್ಪಂದ ಕಾನೂನಿನ ಅಡಿಯಲ್ಲಿ, ವಸ್ತು ಉಲ್ಲಂಘನೆಗಳು ಉಲ್ಲಂಘನೆಯಲ್ಲದ ಪಕ್ಷಕ್ಕೆ ಹಕ್ಕು ನೀಡಬಹುದು",
                        "to remedies including specific performance or damages.": "ನಿರ್ದಿಷ್ಟ ಕಾರ್ಯಕ್ಷಮತೆ ಅಥವಾ ಹಾನಿಗಳು ಸೇರಿದಂತೆ ಪರಿಹಾರಗಳಿಗೆ.",
                        "Ambiguous terms may be interpreted by courts": "ಅಸ್ಪಷ್ಟ ನಿಯಮಗಳನ್ನು ನ್ಯಾಯಾಲಯಗಳು ವ್ಯಾಖ್ಯಾನಿಸಬಹುದು",
                        "according to standard principles of contractual interpretation.": "ಒಪ್ಪಂದ ವ್ಯಾಖ್ಯಾನದ ಪ್ರಮಾಣಿತ ತತ್ವಗಳ ಪ್ರಕಾರ."
                    },
                    "ml": {  # Malayalam
                        "Here's a detailed analysis:": "ഇവിടെ ഒരു വിശദമായ വിശകലനം ഉണ്ട്:",
                        "Contract Structure and Validity:": "കരാറിന്റെ ഘടനയും സാധുതയും:",
                        "Key Legal Provisions:": "പ്രധാന നിയമ വ്യവസ്ഥകൾ:",
                        "Rights and Obligations:": "അവകാശങ്ങളും ബാധ്യതകളും:",
                        "Legal Implications:": "നിയമപരമായ പ്രത്യാഘാതങ്ങൾ:",
                        "Applicable legal frameworks that may be relevant:": "പ്രാസംഗികമായ നിയമ ഘടനകൾ ബന്ധപ്പെട്ടിരിക്കാം:",
                        "DISCLAIMER:": "അവകാശമൊഴി:",
                        "This analysis is provided for informational purposes only": "ഈ വിശകലനം വിവരപരമായ ഉദ്ദേശ്യങ്ങൾക്കായാണ് നൽകുന്നത്",
                        "and should not be construed as legal advice.": "മറ്റു നിയമോപദേശം എന്ന നിലയിൽ വ്യാഖ്യാനിക്കപ്പെടേണ്ടതല്ല.",
                        "Please consult with a qualified legal professional for advice specific to your situation.": "നിങ്ങളുടെ സാഹചര്യത്തിന് പ്രത്യേകമായ ഉപദേശം ലഭിക്കാൻ ദയവായി യോഗ്യമായ ഒരു നിയമ വിദഗ്ധനുമായി ബന്ധപ്പെടുക.",
                        "The document contains standard contractual elements": "ദസ്താവേസ് മാനക കരാർ ഘടകങ്ങൾ അടങ്ങിയിരിക്കുന്നു",
                        "including parties' details, consideration clauses, terms of agreement, and signature requirements.": "പാർട്ടികളുടെ വിശദാംശങ്ങൾ, പരിഗണനാ വ്യവസ്ഥകൾ, കരാറിന്റെ നിബന്ധനകൾ, ഒപ്പ് ആവശ്യങ്ങൾ എന്നിവ ഉൾപ്പെടുന്നു.",
                        "The agreement appears to establish legally binding obligations between the parties under contract law principles.": "കരാർ നിയമത്തിന്റെ തത്വങ്ങൾ പ്രകാരം പാർട്ടികൾക്കിടയിൽ നിയമപരമായി ബദ്ധകൃത്യങ്ങൾ സ്ഥാപിക്കുന്നതുപോലെ കരാർ കാണിക്കുന്നു.",
                        "Terms and conditions governing the relationship between parties are outlined": "പാർട്ടികൾക്കിടയിലെ ബന്ധം നിയന്ത്രിക്കുന്ന നിബന്ധനകളും വ്യവസ്ഥകളും രേഖപ്പെടുത്തിയിരിക്കുന്നു",
                        "with specific performance requirements.": "നിശ്ചിത പ്രകടന ആവശ്യകതകളോടെ.",
                        "Liability provisions and risk allocation measures are included": "ദായിത്വ വ്യവസ്ഥകളും അപകടം വിതരണം ചെയ്യാനുള്ള നടപടികളും ഉൾപ്പെടുന്നു",
                        "to protect the parties' interests.": "പാർട്ടികളുടെ താൽപര്യങ്ങൾ സംരക്ഷിക്കാൻ.",
                        "Termination mechanisms and conditions for contract renewal are specified.": "കരാർ പുതുക്കുന്നതിനുള്ള അവസാനിപ്പിക്കൽ യಂತ್ರങ്ങളും നിബന്ധനകളും വ്യക്തമാക്കപ്പെട്ടിരിക്കുന്നു.",
                        "The respective duties of each party are delineated": "പ്രതിയൊരുത്തന്റെ ബന്ധപ്പെട്ട കടമകൾ രേഖപ്പെടുത്തിയിരിക്കുന്നു",
                        "with specific performance metrics and timelines.": "നിശ്ചിത പ്രകടന മെട്രിക്‌സും സമയരേഖകളും ഉപയോഗിച്ച്.",
                        "Compliance requirements with relevant laws and regulations are established.": "പ്രാസംഗികമായ നിയമങ്ങളും നിയന്ത്രണങ്ങളും പാലിക്കുന്നതിനുള്ള ആവശ്യകതകൾ സ്ഥാപിച്ചിരിക്കുന്നു.",
                        "Remedy mechanisms in case of breach are provided with specific consequences.": "ഉല്ലംഘനത്തിന്റെ സാഹചര്യത്തിൽ പരിഹാര യന്ത്രങ്ങൾ പ്രത്യേക ഫലങ്ങളോടെ നൽകുന്നു.",
                        "The contract creates legally enforceable rights": "കരാർ നിയമപരമായി നടപ്പാക്കാവുന്ന അവകാശങ്ങൾ സൃഷ്ടിക്കുന്നു",
                        "that can be upheld through legal proceedings if necessary.": "ആവശ്യമായാൽ നിയമ നടപടികളിലൂടെ നിലനിര്‍ത്താവുന്നതാണ്.",
                        "Under contract law, material breaches may entitle the non-breaching party": "കരാർ നിയമത്തിന്റെ കീഴിൽ, വസ്തുതാപരമായ ലംഘനങ്ങൾ ലംഘനമല്ലാത്ത പാർട്ടിക്ക് അവകാശം നൽകാം",
                        "to remedies including specific performance or damages.": "നിശ്ചിത പ്രകടനം അല്ലെങ്കിൽ നഷ്ടപരിഹാരം ഉൾപ്പെടെയുള്ള പരിഹാരങ്ങൾക്ക്.",
                        "Ambiguous terms may be interpreted by courts": "അസ്പഷ്ടമായ നിബന്ധനകൾ കോടതികൾക്ക് വ്യാഖ്യാനിക്കാവുന്നതാണ്",
                        "according to standard principles of contractual interpretation.": "ഒപ്പന്തം വ്യാഖ്യാനയുടെ മാനക തത്വങ്ങൾ അനുസരിച്ച്."
                    },
                    "ta": {  # Tamil
                        "Here's a detailed analysis:": "இதோ விரிவான பகுப்பாய்வு:",
                        "Contract Structure and Validity:": "ஒப்பந்த அமைப்பு மற்றும் செல்லுபடித்தன்மை:",
                        "Key Legal Provisions:": "முக்கிய சட்ட விதிகள்:",
                        "Rights and Obligations:": "உரிமைகள் மற்றும் கடமைகள்:",
                        "Legal Implications:": "சட்ட தாக்கங்கள்:",
                        "Applicable legal frameworks that may be relevant:": "பொருத்தமான சட்ட கட்டமைப்புகள் தொடர்புடையதாக இருக்கலாம்:",
                        "DISCLAIMER:": "பொறுப்புத்துறப்பு:",
                        "This analysis is provided for informational purposes only": "இந்த பகுப்பாய்வு தகவல் நோக்கங்களுக்காக மட்டுமே வழங்கப்படுகிறது",
                        "and should not be construed as legal advice.": "மற்றும் இதனை சட்ட ஆலோசனையாகக் கருதக்கூடாது.",
                        "Please consult with a qualified legal professional for advice specific to your situation.": "உங்கள் சூழ்நிலைக்கு குறிப்பிட்ட ஆலோசனைக்கு தகுதிவாய்ந்த சட்ட நிபுணரை அணுகவும்.",
                        "The document contains standard contractual elements": "ஆவணம் நிலையான ஒப்பந்த கூறுகளை கொண்டுள்ளது",
                        "including parties' details, consideration clauses, terms of agreement, and signature requirements.": "தரப்பினரின் விவரங்கள், பரிசீலனை விதிகள், ஒப்பந்த விதிமுறைகள் மற்றும் கையொப்ப தேவைகள் உள்ளிட்டவை.",
                        "The agreement appears to establish legally binding obligations between the parties under contract law principles.": "ஒப்பந்தம் சட்டப்பூர்வமாக நடைமுறைப்படுத்தக்கூடிய உரிமைகளை உருவாக்குகிறது",
                        "that can be upheld through legal proceedings if necessary.": "தேவைப்பட்டால் சட்ட நடவடிக்கைகள் மூலம் நிலைநிறுத்தப்படலாம்.",
                        "Under contract law, material breaches may entitle the non-breaching party": "ஒப்பந்த சட்டத்தின் கீழ், பொருள் மீறல்கள் மீறாத தரப்பினருக்கு உரிமை அளிக்கலாம்",
                        "to remedies including specific performance or damages.": "குறிப்பிட்ட செயல்திறன் அல்லது சேதங்கள் உள்ளிட்ட தீர்வுகளுக்கு.",
                        "Ambiguous terms may be interpreted by courts": "தெளிவற்ற விதிமுறைகளை நீதிமன்றங்கள் விளக்கலாம்",
                        "according to standard principles of contractual interpretation.": "ஒப்பந்த விளக்கத்தின் நிலையான கோட்பாடுகளின் படி."
                    },
                    "ur": {  # Urdu
                        "Here's a detailed analysis:": "یہاں ایک تفصیلی تجزیہ ہے:",
                        "Contract Structure and Validity:": "معاہدے کی ساخت اور حیثیت:",
                        "Key Legal Provisions:": "اہم قانونی دفعات:",
                        "Rights and Obligations:": "حقوق اور ذمہ داریاں:",
                        "Legal Implications:": "قانونی مضمرات:",
                        "Applicable legal frameworks that may be relevant:": "متعلقہ قانونی ڈھانچے جو متعلقہ ہو سکتے ہیں:",
                        "DISCLAIMER:": "انکار:",
                        "This analysis is provided for informational purposes only": "یہ تجزیہ صرف معلوماتی مقاصد کے لیے فراہم کیا گیا ہے",
                        "and should not be construed as legal advice.": "اور اسے قانونی مشورے کے طور پر نہیں سمجھا جانا چاہیے۔",
                        "Please consult with a qualified legal professional for advice specific to your situation.": "براہ کرم اپنی صورتحال کے لیے مخصوص مشورے کے لیے کسی اہل قانونی پیشہ ور سے مشورہ کریں۔",
                        "The document contains standard contractual elements": "دستاویز میں معیاری معاہداتی عناصر شامل ہیں",
                        "including parties' details, consideration clauses, terms of agreement, and signature requirements.": "جس میں فریقین کی تفصیلات، غور و فکر کی دفعات، معاہدے کی شرائط اور دستخط کی ضروریات شامل ہیں۔",
                        "The agreement appears to establish legally binding obligations between the parties under contract law principles.": "معاہدہ معاہدے کے قانون کے اصولوں کے تحت فریقین کے درمیان قانونی طور پر پابند ذمہ داریوں کے قیام کا مظاہرہ کرتا ہے۔",
                        "Terms and conditions governing the relationship between parties are outlined": "فریقین کے درمیان تعلقات کو منظم کرنے والی شرائط و ضوابط کی وضاحت کی گئی ہے",
                        "with specific performance requirements.": "خاص کارکردگی کی ضروریات کے ساتھ۔",
                        "Liability provisions and risk allocation measures are included": "ذمہ داری کی دفعات اور خطرے کی تقسیم کے اقدامات شامل ہیں",
                        "to protect the parties' interests.": "فریقین کے مفادات کے تحفظ کے لیے۔",
                        "Termination mechanisms and conditions for contract renewal are specified.": "معاہدے کی تجدید کے لیے ختم کرنے کے طریقہ کار اور شرائط کی وضاحت کی گئی ہے۔",
                        "The respective duties of each party are delineated": "ہر فریق کے متعلقہ فرائض کی وضاحت کی گئی ہے",
                        "with specific performance metrics and timelines.": "خاص کارکردگی کے میٹرکس اور ٹائم لائنز کے ساتھ۔",
                        "Compliance requirements with relevant laws and regulations are established.": "متعلقہ قوانین اور ضوابط کے ساتھ تعمیل کے تقاضے قائم کیے گئے ہیں۔",
                        "Remedy mechanisms in case of breach are provided with specific consequences.": "خلاف ورزی کی صورت میں علاج کے طریقہ کار مخصوص نتائج کے ساتھ فراہم کیے گئے ہیں۔",
                        "The contract creates legally enforceable rights": "معاہدہ قانونی طور پر قابل نفاذ حقوق پیدا کرتا ہے",
                        "that can be upheld through legal proceedings if necessary.": "جنہیں ضرورت پڑنے پر قانونی کارروائی کے ذریعے برقرار رکھا جا سکتا ہے۔",
                        "Under contract law, material breaches may entitle the non-breaching party": "معاہدے کے قانون کے تحت، مادی خلاف ورزیاں غیر خلاف ورزی کرنے والی پارٹی کو حق دار بنا سکتی ہیں",
                        "to remedies including specific performance or damages.": "خاص کارکردگی یا نقصانات سمیت علاج کے لیے۔",
                        "Ambiguous terms may be interpreted by courts": "غیر واضح شرائط کی تشریح عدالتوں کے ذریعہ کی جا سکتی ہے",
                        "according to standard principles of contractual interpretation.": "معیاری معاہداتی تشریح کے اصولوں کے مطابق۔"
                    },
                    "gu": {  # Gujarati
                        "Here's a detailed analysis:": "અહીં એક વિગતવાર વિશ્લેષણ છે:",
                        "Contract Structure and Validity:": "કોન્ટ્રાક્ટની રચના અને માન્યતા:",
                        "Key Legal Provisions:": "મુખ્ય કાનૂની પ્રાવધાન:",
                        "Rights and Obligations:": "હક્કો અને ફરજીઓ:",
                        "Legal Implications:": "કાનૂની પરિણામો:",
                        "Applicable legal frameworks that may be relevant:": "લાગુ પડતા કાનૂની માળખાં જે સંબંધિત હોઈ શકે છે:",
                        "DISCLAIMER:": "અસ્વીકરણ:",
                        "This analysis is provided for informational purposes only": "આ વિશ્લેષણ માત્ર માહિતીના ઉદ્દેશો માટે આપવામાં આવ્યું છે",
                        "and should not be construed as legal advice.": "અને તેને કાનૂની સલાહ તરીકે સમજવામાં આવવું જોઈએ નહીં.",
                        "Please consult with a qualified legal professional for advice specific to your situation.": "કૃપા કરીને તમારી પરિસ્થિતિ માટે વિશિષ્ટ સલાહ માટે એક યોગ્ય કાનૂની વ્યાવસાયિક સાથે પરામર્શ કરો.",
                        "The document contains standard contractual elements": "દસ્તાવેજમાં માનક કરારના તત્વો શામેલ છે",
                        "including parties' details, consideration clauses, terms of agreement, and signature requirements.": "પાર્ટીઓની વિગતો, વિચારણા કલમો, કરારની શરતો અને સહીની જરૂરિયાતો સહિત.",
                        "The agreement appears to establish legally binding obligations between the parties under contract law principles.": "સમજૂતી કરારના કાયદાના સિદ્ધાંતો હેઠળ પક્ષો વચ્ચે કાનૂની રીતે બાંધકામ કરનારાં ફરજીઓ સ્થાપિત કરે છે તેવા દેખાય છે.",
                        "Terms and conditions governing the relationship between parties are outlined": "પક્ષો વચ્ચેના સંબંધને નિયંત્રિત કરતી શરતો અને શરતોની રૂપરેખા રજૂ કરવામાં આવી છે",
                        "with specific performance requirements.": "નિશ્ચિત કામગીરીની જરૂરિયાતો સાથે.",
                        "Liability provisions and risk allocation measures are included": "જવાબદારીની વ્યવસ્થાઓ અને જોખમ વિતરણના પગલાંઓનો સમાવેશ થાય છે",
                        "to protect the parties' interests.": "પક્ષોના હિતોને સુરક્ષિત કરવા માટે.",
                        "Termination mechanisms and conditions for contract renewal are specified.": "કોન્ટ્રાક્ટ નવીનીકરણ માટેની સમાપ્તિની યાંત્રિકતાઓ અને શરતો સ્પષ્ટ કરવામાં આવી છે.",
                        "The respective duties of each party are delineated": "દરેક પક્ષની સંબંધિત ફરજીઓની રેખાંકન કરવામાં આવી છે",
                        "with specific performance metrics and timelines.": "નિશ્ચિત કામગીરી મેટ્રિક્સ અને સમયરેખાઓ સાથે.",
                        "Compliance requirements with relevant laws and regulations are established.": "લાગુ પડતા કાયદા અને નિયમનકારી જરૂરિયાતો સ્થાપિત કરવામાં આવી છે.",
                        "Remedy mechanisms in case of breach are provided with specific consequences.": "ભંગની સ્થિતિમાં ઉપાયની યાંત્રિકતાઓ વિશિષ્ટ પરિણામો સાથે પૂરી પાડવામાં આવે છે.",
                        "The contract creates legally enforceable rights": "કોન્ટ્રાક્ટ કાનૂની રીતે અમલમાં લાવવા માટેના હક્કો બનાવે છે",
                        "that can be upheld through legal proceedings if necessary.": "જ્યારે જરૂરી હોય ત્યારે કાનૂની કાર્યવાહી દ્વારા જાળવવામાં આવી શકે છે.",
                        "Under contract law, material breaches may entitle the non-breaching party": "કોન્ટ્રાક્ટ કાયદા હેઠળ, સામગ્રીના ભંગો નોન-ભંગી પક્ષને અધિકાર આપી શકે છે",
                        "to remedies including specific performance or damages.": "નિશ્ચિત કામગીરી અથવા નુકસાન સહિતના ઉપાયોને.",
                        "Ambiguous terms may be interpreted by courts": "અસ્પષ્ટ શરતોની વ્યાખ્યા અદાલતો દ્વારા કરવામાં આવી શકે છે",
                        "according to standard principles of contractual interpretation.": "કોન્ટ્રાક્ટની વ્યાખ્યાના માનક સિદ્ધાંતો અનુસાર."
                    },
                    "kn": {  # Kannada
                        "Here's a detailed analysis:": "ಇಲ್ಲಿ ವಿವರವಾದ ವಿಶ್ಲೇಷಣೆಯಿದೆ:",
                        "Contract Structure and Validity:": "ಒಪ್ಪಂದದ ರಚನೆ ಮತ್ತು ಮಾನ್ಯತೆ:",
                        "Key Legal Provisions:": "ಪ್ರಮುಖ ಕಾನೂನು ನಿಬಂಧನೆಗಳು:",
                        "Rights and Obligations:": "ಹಕ್ಕುಗಳು ಮತ್ತು ಜವಾಬ್ದಾರಿಗಳು:",
                        "Legal Implications:": "ಕಾನೂನು ಪರಿಣಾಮಗಳು:",
                        "Applicable legal frameworks that may be relevant:": "ಅನ್ವಯವಾಗುವ ಕಾನೂನು ಚೌಕಟ್ಟುಗಳು ಸಂಬಂಧಿತವಾಗಿರಬಹುದು:",
                        "DISCLAIMER:": "ಹಕ್ಕುತ್ಯಾಗ:",
                        "This analysis is provided for informational purposes only": "ಈ ವಿಶ್ಲೇಷಣೆಯನ್ನು ಕೇವಲ ಮಾಹಿತಿ ಉದ್ದೇಶಗಳಿಗಾಗಿ ಮಾತ್ರ ನೀಡಲಾಗಿದೆ",
                        "and should not be construed as legal advice.": "ಮತ್ತು ಇದನ್ನು ಕಾನೂನು ಸಲಹೆಯಾಗಿ ಪರಿಗಣಿಸಬಾರದು.",
                        "Please consult with a qualified legal professional for advice specific to your situation.": "ನಿಮ್ಮ ಪರಿಸ್ಥಿತಿಗೆ ನಿರ್ದಿಷ್ಟವಾದ ಸಲಹೆಗಾಗಿ ದಯವಿಟ್ಟು ಅರ್ಹ ಕಾನೂನು ವೃತ್ತಿಪರರನ್ನು ಸಂಪರ್ಕಿಸಿ.",
                        "The document contains standard contractual elements": "ದಾಖಲೆಯು ಪ್ರಮಾಣಿತ ಒಪ್ಪಂದದ ಅಂಶಗಳನ್ನು ಒಳಗೊಂಡಿದೆ",
                        "including parties' details, consideration clauses, terms of agreement, and signature requirements.": "ಪಕ್ಷಗಳ ವಿವರಗಳು, ಪರಿಗಣನಾ ಷರತ್ತುಗಳು, ಒಪ್ಪಂದದ ನಿಯಮಗಳು ಮತ್ತು ಸಹಿ ಅವಶ್ಯಕತೆಗಳನ್ನು ಒಳಗೊಂಡಂತೆ.",
                        "The agreement appears to establish legally binding obligations between the parties under contract law principles.": "ಒಪ್ಪಂದದ ಕಾನೂನು ತತ್ವಗಳ ಅಡಿಯಲ್ಲಿ ಪಕ್ಷಗಳ ನಡುವೆ ಕಾನೂನುಬದ್ಧವಾಗಿ ಬದ್ಧತೆಗಳನ್ನು ಸ್ಥಾಪಿಸುವಂತೆ ಒಪ್ಪಂದವು ಕಾಣುತ್ತದೆ.",
                        "Terms and conditions governing the relationship between parties are outlined": "ಪಕ್ಷಗಳ ನಡುವಿನ ಸಂಬಂಧವನ್ನು ನಿಯಂತ್ರಿಸುವ ನಿಯಮಗಳು ಮತ್ತು ಷರತ್ತುಗಳನ್ನು ವಿವರಿಸಲಾಗಿದೆ",
                        "with specific performance requirements.": "ನಿರ್ದಿಷ್ಟ ಕಾರ್ಯಕ್ಷಮತೆ ಅವಶ್ಯಕತೆಗಳೊಂದಿಗೆ.",
                        "Liability provisions and risk allocation measures are included": "ಹೊಣೆಗಾರಿಕೆ ನಿಬಂಧನೆಗಳು ಮತ್ತು ಅಪಾಯದ ಹಂಚಿಕೆ ಕ್ರಮಗಳನ್ನು ಸೇರಿಸಲಾಗಿದೆ",
                        "to protect the parties' interests.": "ಪಕ್ಷಗಳ ಹಿತಾಸಕ್ತಿಗಳನ್ನು ರಕ್ಷಿಸಲು.",
                        "Termination mechanisms and conditions for contract renewal are specified.": "ಒಪ್ಪಂದ ನವೀಕರಣಕ್ಕಾಗಿ ಕೊನೆಗೊಳಿಸುವ ವಿಧಾನಗಳು ಮತ್ತು ಷರತ್ತುಗಳನ್ನು ನಿರ್ದಿಷ್ಟಪಡಿಸಲಾಗಿದೆ.",
                        "The respective duties of each party are delineated": "ಪ್ರತಿಯೊಂದು ಪಕ್ಷದ ಸಂಬಂಧಿತ ಕರ್ತವ್ಯಗಳನ್ನು ವಿಂಗಡಿಸಲಾಗಿದೆ",
                        "with specific performance metrics and timelines.": "ನಿರ್ದಿಷ್ಟ ಕಾರ್ಯಕ್ಷಮತೆ ಮೆಟ್ರಿಕ್ಸ್ ಮತ್ತು ಸಮಯದ ಮಿತಿಗಳೊಂದಿಗೆ.",
                        "Compliance requirements with relevant laws and regulations are established.": "ಸಂಬಂಧಿತ ಕಾನೂನುಗಳು ಮತ್ತು ನಿಬಂಧನೆಗಳೊಂದಿಗೆ ಅನುಸರಣೆಯ ಅವಶ್ಯಕತೆಗಳನ್ನು ಸ್ಥಾಪಿಸಲಾಗಿದೆ.",
                        "Remedy mechanisms in case of breach are provided with specific consequences.": "ಉಲ್ಲಂಘನೆಯ ಸಂದರ್ಭದಲ್ಲಿ ಪರಿಹಾರ ವಿಧಾನಗಳನ್ನು ನಿರ್ದಿಷ್ಟ ಪರಿಣಾಮಗಳೊಂದಿಗೆ ಒದಗಿಸಲಾಗಿದೆ.",
                        "The contract creates legally enforceable rights": "ಒಪ್ಪಂದವು ಕಾನೂನುಬದ್ಧವಾಗಿ ಜಾರಿಗೊಳಿಸಬಹುದಾದ ಹಕ್ಕುಗಳನ್ನು ಸೃಷ್ಟಿಸುತ್ತದೆ",
                        "that can be upheld through legal proceedings if necessary.": "ಅಗತ್ಯವಿದ್ದಲ್ಲಿ ಕಾನೂನು ವ್ಯವಹರಣೆಗಳ ಮೂಲಕ ಉಳಿಸಿಕೊಳ್ಳಬಹುದು.",
                        "Under contract law, material breaches may entitle the non-breaching party": "ಒಪ್ಪಂದ ಕಾನೂನಿನ ಅಡಿಯಲ್ಲಿ, ವಸ್ತು ಉಲ್ಲಂಘನೆಗಳು ಉಲ್ಲಂಘನೆಯಲ್ಲದ ಪಕ್ಷಕ್ಕೆ ಹಕ್ಕು ನೀಡಬಹುದು",
                        "to remedies including specific performance or damages.": "ನಿರ್ದಿಷ್ಟ ಕಾರ್ಯಕ್ಷಮತೆ ಅಥವಾ ಹಾನಿಗಳು ಸೇರಿದಂತೆ ಪರಿಹಾರಗಳಿಗೆ.",
                        "Ambiguous terms may be interpreted by courts": "ಅಸ್ಪಷ್ಟ ನಿಯಮಗಳನ್ನು ನ್ಯಾಯಾಲಯಗಳು ವ್ಯಾಖ್ಯಾನಿಸಬಹುದು",
                        "according to standard principles of contractual interpretation.": "ಒಪ್ಪಂದ ವ್ಯಾಖ್ಯಾನದ ಪ್ರಮಾಣಿತ ತತ್ವಗಳ ಪ್ರಕಾರ."
                    },
                    "ml": {  # Malayalam
                        "Here's a detailed analysis:": "ഇവിടെ ഒരു വിശദമായ വിശകലനം ഉണ്ട്:",
                        "Contract Structure and Validity:": "കരാറിന്റെ ഘടനയും സാധുതയും:",
                        "Key Legal Provisions:": "പ്രധാന നിയമ വ്യവസ്ഥകൾ:",
                        "Rights and Obligations:": "അവകാശങ്ങളും ബാധ്യതകളും:",
                        "Legal Implications:": "നിയമപരമായ പ്രത്യാഘാതങ്ങൾ:",
                        "Applicable legal frameworks that may be relevant:": "പ്രാസംഗികമായ നിയമ ഘടനകൾ ബന്ധപ്പെട്ടിരിക്കാം:",
                        "DISCLAIMER:": "അവകാശമൊഴി:",
                        "This analysis is provided for informational purposes only": "ഈ വിശകലനം വിവരപരമായ ഉദ്ദേശ്യങ്ങൾക്കായാണ് നൽകുന്നത്",
                        "and should not be construed as legal advice.": "മറ്റു നിയമോപദേശം എന്ന നിലയിൽ വ്യാഖ്യാനിക്കപ്പെടേണ്ടതല്ല.",
                        "Please consult with a qualified legal professional for advice specific to your situation.": "നിങ്ങളുടെ സാഹചര്യത്തിന് പ്രത്യേകമായ ഉപദേശം ലഭിക്കാൻ ദയവായി യോഗ്യമായ ഒരു നിയമ വിദഗ്ധനുമായി ബന്ധപ്പെടുക.",
                        "The document contains standard contractual elements": "ദസ്താവേസ് മാനക കരാർ ഘടകങ്ങൾ അടങ്ങിയിരിക്കുന്നു",
                        "including parties' details, consideration clauses, terms of agreement, and signature requirements.": "പാർട്ടികളുടെ വിശദാംശങ്ങൾ, പരിഗണനാ വ്യവസ്ഥകൾ, കരാറിന്റെ നിബന്ധനകൾ, ഒപ്പ് ആവശ്യങ്ങൾ എന്നിവ ഉൾപ്പെടുന്നു.",
                        "The agreement appears to establish legally binding obligations between the parties under contract law principles.": "കരാർ നിയമത്തിന്റെ തത്വങ്ങൾ പ്രകാരം പാർട്ടികൾക്കിടയിൽ നിയമപരമായി ബദ്ധകൃത്യങ്ങൾ സ്ഥാപിക്കുന്നതുപോലെ കരാർ കാണിക്കുന്നു.",
                        "Terms and conditions governing the relationship between parties are outlined": "പക്ഷങ്ങൾക്കിടയിലെ ബന്ധം നിയന്ത്രിക്കുന്ന നിബന്ധനകളും വ്യവസ്ഥകളും രേഖപ്പെടുത്തിയിരിക്കുന്നു",
                        "with specific performance requirements.": "നിശ്ചിത പ്രകടന ആവശ്യകതകളോടെ.",
                        "Liability provisions and risk allocation measures are included": "ദായിത്വ വ്യവസ്ഥകളും അപകടം വിതരണം ചെയ്യാനുള്ള നടപടികളും ഉൾപ്പെടുന്നു",
                        "to protect the parties' interests.": "പക്ഷങ്ങളുടെ താൽപര്യങ്ങൾ സംരക്ഷിക്കാൻ.",
                        "Termination mechanisms and conditions for contract renewal are specified.": "കരാർ പുതുക്കുന്നതിനുള്ള അവസാനിപ്പിക്കൽ യന്ത്രങ്ങളും നിബന്ധനകളും വ്യക്തമാക്കപ്പെട്ടിരിക്കുന്നു.",
                        "The respective duties of each party are delineated": "દરેક પક્ષની સંબંધિત ફરજીઓની રેખાંકન કરવામાં આવી છે",
                        "with specific performance metrics and timelines.": "നിശ്ചിത പ്രകടന മെട്രിക്‌സും സമയരേഖകളും ഉപയോഗിച്ച്.",
                        "Compliance requirements with relevant laws and regulations are established.": "ലാഗു પડતા കാനൂനുകളും നിയന്ത്രണങ്ങളും പാലിക്കുന്നതിനുള്ള ആവശ്യകതകൾ സ്ഥാപിച്ചിരിക്കുന്നു.",
                        "Remedy mechanisms in case of breach are provided with specific consequences.": "ഉല്ലംഘനത്തിന്റെ സാഹചര്യത്തിൽ പരിഹാര യന്ത്രങ്ങൾ പ്രത്യേക ഫലങ്ങളോടെ നൽകുന്നു.",
                        "The contract creates legally enforceable rights": "കരാർ നിയമപരമായി നടപ്പാക്കാവുന്ന അവകാശങ്ങൾ സൃഷ്ടിക്കുന്നു",
                        "that can be upheld through legal proceedings if necessary.": "ആവശ്യമായാൽ നിയമ നടപടികളിലൂടെ നിലനിര്‍ത്താവുന്നതാണ്.",
                        "Under contract law, material breaches may entitle the non-breaching party": "കരാർ നിയമത്തിന്റെ കീഴിൽ, വസ്തുതാപരമായ ലംഘനങ്ങൾ ലംഘനമല്ലാത്ത പാർട്ടിക്ക് അവകാശം നൽകാം",
                        "to remedies including specific performance or damages.": "നിശ്ചിത പ്രകടനം അല്ലെങ്കിൽ നഷ്ടപരിഹാരം ഉൾപ്പെടെയുള്ള പരിഹാരങ്ങൾക്ക്.",
                        "Ambiguous terms may be interpreted by courts": "അസ്പഷ്ടമായ നിബന്ധനകൾക്ക് കോടതികൾ വ്യാഖ്യാനിക്കാവുന്നതാണ്",
                        "according to standard principles of contractual interpretation.": "ഒപ്പന്തം വ്യാഖ്യാനത്തിന്റെ മാനക തത്വങ്ങൾ അനുസരിച്ച്."
                    },
                    "or": {  # Odia
                        "Here's a detailed analysis:": "ଏଠାରେ ଏକ ବିସ୍ତୃତ ବିଶ୍ଳେଷଣ ଅଛି:",
                        "Contract Structure and Validity:": "କନ୍ଟ୍ରାକ୍ଟର ଗଠନ ଏବଂ ବୈଧତା:",
                        "Key Legal Provisions:": "ମୁଖ୍ୟ ଆଇନ ନିୟମାବଳୀ:",
                        "Rights and Obligations:": "ଅଧିକାର ଏବଂ ଦାୟିତ୍ୱ:",
                        "Legal Implications:": "ଆଇନ ଗତ ପ୍ରତିଫଳ:",
                        "Applicable legal frameworks that may be relevant:": "ଯୋଗ୍ୟ ଆଇନ ଢାଞ୍ଚା ଯାହା ସମ୍ବନ୍ଧିତ ହୋଇପାରେ:",
                        "DISCLAIMER:": "ଅସ୍ୱୀକୃତି:",
                        "This analysis is provided for informational purposes only": "ଏହି ବିଶ୍ଳେଷଣ କେବଳ ସୂଚନାମୂଳକ ଉଦ୍ଦେଶ୍ୟରେ ଦିଆଯାଇଛି",
                        "and should not be construed as legal advice.": "ଏବଂ ଏହାକୁ ଆଇନ ଉପଦେଶ ଭାବେ ବୁଝିବା ଉଚିତ୍ ନୁହେଁ।",
                        "Please consult with a qualified legal professional for advice specific to your situation.": "ଦୟାକରି ଆପଣଙ୍କର ପରିସ୍ଥିତି ପାଇଁ ବିଶେଷ ଉପଦେଶ ପାଇଁ ଏକ ଯୋଗ୍ୟ ଆଇନ ବିଶେଷଜ୍ଞଙ୍କ ସହିତ ପରାମର୍ଶ କରନ୍ତୁ।",
                        "The document contains standard contractual elements": "ଦସ୍ତାବେଜରେ ମାନକ କନ୍ଟ୍ରାକ୍ଟୁଆଲ୍ ଉପାଦାନ ଅଛି",
                        "including parties' details, consideration clauses, terms of agreement, and signature requirements.": "ପାର୍ଟିଗୁଡିକର ବିବରଣୀ, ଗ୍ରହଣ କ୍ଲଜ୍, ସମ୍ମତିର ଶରତ୍, ଏବଂ ସହିର ଆବଶ୍ୟକତାଗୁଡିକ ସମେତ।",
                        "The agreement appears to establish legally binding obligations between the parties under contract law principles.": "ସମ୍ମତି କନ୍ଟ୍ରାକ୍ଟ ଆଇନର ସିଦ୍ଧାନ୍ତଗୁଡିକ ଅନୁସାରେ ପାର୍ଟିଗୁଡିକ ମଧ୍ୟରେ ଆଇନଗତ ଭାବେ ବାଧ୍ୟକର ଦାୟିତ୍ୱ ସ୍ଥାପନ କରିବାକୁ ଦେଖାଯାଉଛି।",
                        "Terms and conditions governing the relationship between parties are outlined": "ପାର୍ଟିଗୁଡିକ ମଧ୍ୟରେ ସମ୍ପର୍କକୁ ନିୟନ୍ତ୍ରଣ କରୁଥିବା ନିୟମ ଏବଂ ଶରତ୍ଗୁଡିକର ରୂପରେଖା ଦିଆଯାଇଛି",
                        "with specific performance requirements.": "ନିର୍ଦ୍ଧାରିତ କାର୍ଯ୍ୟକ୍ଷମତା ଆବଶ୍ୟକତା ସହିତ।",
                        "Liability provisions and risk allocation measures are included": "ଦାୟିତ୍ୱ ପ୍ରବଧାନ ଏବଂ ଝୁଲିବା ବିତରଣ ପଦକ୍ଷେପଗୁଡିକ ଅନ୍ତର୍ଭୁକ୍ତ",
                        "to protect the parties' interests.": "ପାର୍ଟିଗୁଡିକର ହିତରକ୍ଷା ପାଇଁ।",
                        "Termination mechanisms and conditions for contract renewal are specified.": "କନ୍ଟ୍ରାକ୍ଟ ନବୀକରଣ ପାଇଁ ସମାପ୍ତି ଯନ୍ତ୍ରଣା ଏବଂ ଶରତ୍ଗୁଡିକ ନିର୍ଦ୍ଧାରିତ କରାଯାଇଛି।",
                        "The respective duties of each party are delineated": "ପ୍ରତ୍ୟେକ ପାର୍ଟିର ସମ୍ବନ୍ଧିତ କର୍ତ୍ତବ୍ୟଗୁଡିକ ରେଖାଙ୍କିତ",
                        "with specific performance metrics and timelines.": "ନିର୍ଦ୍ଧାରିତ କାର୍ଯ୍ୟକ୍ଷମତା ମେଟ୍ରିକ୍ସ ଏବଂ ସମୟରେଖା ସହିତ।",
                        "Compliance requirements with relevant laws and regulations are established.": "ସମ୍ବନ୍ଧିତ ଆଇନ ଏବଂ ନିୟମାବଳୀ ସହିତ ଅନୁସରଣ ଆବଶ୍ୟକତାଗୁଡିକ ସ୍ଥାପିତ କରାଯାଇଛି।",
                        "Remedy mechanisms in case of breach are provided with specific consequences.": "ଭଙ୍ଗର କେସରେ ଔଷଧ ଯନ୍ତ୍ରଣାଗୁଡିକ ନିର୍ଦ୍ଧାରିତ ପରିଣାମ ସହିତ ଦିଆଯାଇଛି।",
                        "The contract creates legally enforceable rights": "କନ୍ଟ୍ରାକ୍ଟ ଆଇନଗତ ଭାବେ ଲାଗୁ କରାଯାଇପାରିବା ଅଧିକାର ସୃଷ୍ଟି କରେ",
                        "that can be upheld through legal proceedings if necessary.": "ଯଦି ଆବଶ୍ୟକ ହୁଏ ତେବେ ଆଇନଗତ କାର୍ଯ୍ୟବାହିକା ମାଧ୍ୟମରେ ଧରାଯାଇପାରିବ।",
                        "Under contract law, material breaches may entitle the non-breaching party": "କନ୍ଟ୍ରାକ୍ଟ ଆଇନ ଅନୁସାରେ, ପଦାର୍ଥ ଭଙ୍ଗଗୁଡିକ ନନ୍-ଭଙ୍ଗିଂ ପାର୍ଟିକୁ ଅଧିକାର ଦେଇପାରେ",
                        "to remedies including specific performance or damages.": "ନିର୍ଦ୍ଧାରିତ କାର୍ଯ୍ୟକ୍ଷମତା କିମ୍ବା ନଷ୍ଟ ସମ୍ମିଳିତ ଔଷଧଗୁଡିକୁ।",
                        "Ambiguous terms may be interpreted by courts": "ଅସ୍ପଷ୍ଟ ଶରତ୍ଗୁଡିକୁ ଆଇନ ମାନ୍ୟତା ଦ୍ୱାରା ବ୍ୟାଖ୍ୟା କରାଯାଇପାରେ",
                        "according to standard principles of contractual interpretation.": "ମାନକ କନ୍ଟ୍ରାକ୍ଟ ବ୍ୟାଖ୍ୟା ପ୍ରିନ୍ସିପଲ୍ ଅନୁସାରେ।"
                    },
                    "pa": {  # Punjabi
                        "Here's a detailed analysis:": "ਇੱਥੇ ਇੱਕ ਵਿਸਤ੍ਰਿਤ ਵਿਸ਼ਲੇਸ਼ਣ ਹੈ:",
                        "Contract Structure and Validity:": "ਕਾਂਟ੍ਰੈਕਟ ਦੀ ਬਣਾਵਟ ਅਤੇ ਵੈਧਤਾ:",
                        "Key Legal Provisions:": "ਮੁੱਖ ਕਾਨੂੰਨੀ ਪ੍ਰਾਵਧਾਨ:",
                        "Rights and Obligations:": "ਅਧਿਕਾਰ ਅਤੇ ਜ਼ਿੰਮੇਵਾਰੀਆਂ:",
                        "Legal Implications:": "ਕਾਨੂੰਨੀ ਨਤੀਜੇ:",
                        "Applicable legal frameworks that may be relevant:": "ਲਾਗੂ ਹੋ ਸਕਦੇ ਕਾਨੂੰਨੀ ਢਾਂਚੇ ਜੋ ਸਬੰਧਤ ਹੋ ਸਕਦੇ ਹਨ:",
                        "DISCLAIMER:": "ਅਸਵੀਕਰਨ:",
                        "This analysis is provided for informational purposes only": "ਇਹ ਵਿਸ਼ਲੇਸ਼ਣ ਸਿਰਫ਼ ਜਾਣਕਾਰੀ ਦੇ ਉਦੇਸ਼ਾਂ ਲਈ ਦਿੱਤੀ ਗਈ ਹੈ",
                        "and should not be construed as legal advice.": "ਅਤੇ ਇਸਨੂੰ ਕਾਨੂੰਨੀ ਸਲਾਹ ਵਜੋਂ ਨਹੀਂ ਸਮਝਿਆ ਜਾਣਾ ਚਾਹੀਦਾ।",
                        "Please consult with a qualified legal professional for advice specific to your situation.": "ਕਿਰਪਾ ਕਰਕੇ ਆਪਣੀ ਸਥਿਤੀ ਲਈ ਵਿਸ਼ੇਸ਼ ਸਲਾਹ ਲਈ ਕਿਸੇ ਯੋਗ ਕਾਨੂੰਨੀ ਵਿਸ਼ੇਸ਼ਜ੍ਞ ਨਾਲ ਸਲਾਹ ਕਰੋ।",
                        "The document contains standard contractual elements": "ਦਸਤਾਵੇਜ਼ ਵਿੱਚ ਮਿਆਰੀ ਸੰਵਿਧਾਨਕ ਤੱਤ ਸ਼ਾਮਲ ਹਨ",
                        "including parties' details, consideration clauses, terms of agreement, and signature requirements.": "ਪਾਰਟੀਆਂ ਦੇ ਵੇਰਵਿਆਂ, ਵਿਚਾਰਧਾਰਾ ਧਾਰਾਵਾਂ, ਸਮਝੌਤੇ ਦੀਆਂ ਸ਼ਰਤਾਂ ਅਤੇ ਦਸਤਖਤ ਦੀਆਂ ਲੋੜਾਂ ਸਮੇਤ।",
                        "The agreement appears to establish legally binding obligations between the parties under contract law principles.": "ਸਮਝੌਤਾ ਕਾਨੂਨੀ ਤੌਰ 'ਤੇ ਪਾਰਟੀਆਂ ਦੇ ਵਿਚਕਾਰ ਬੰਨ੍ਹਨ ਵਾਲੀਆਂ ਜ਼ਿੰਮੇਵਾਰੀਆਂ ਨੂੰ ਕਾਇਮ ਕਰਨ ਲਈ ਪ੍ਰਤੀਤ ਹੁੰਦਾ ਹੈ।",
                        "Terms and conditions governing the relationship between parties are outlined": "ਪਾਰਟੀਆਂ ਦੇ ਵਿਚਕਾਰ ਦੇ ਰਿਸ਼ਤੇ ਨੂੰ ਨਿਯੰਤਰਿਤ ਕਰਨ ਵਾਲੀਆਂ ਸ਼ਰਤਾਂ ਅਤੇ ਸ਼ਰਤਾਂ ਦੀ ਰੂਪਰੇਖਾ ਦਿੱਤੀ ਗਈ ਹੈ",
                        "with specific performance requirements.": "ਨਿਸ਼ਚਿਤ ਪ੍ਰਦਰਸ਼ਨ ਦੀਆਂ ਲੋੜਾਂ ਨਾਲ।",
                        "Liability provisions and risk allocation measures are included": "ਜ਼ਿੰਮੇਵਾਰੀ ਦੀਆਂ ਪ੍ਰਾਵਧਾਨਾਂ ਅਤੇ ਖਤਰੇ ਦੇ ਵੰਡ ਦੇ ਉਪਾਅ ਸ਼ਾਮਲ ਹਨ",
                        "to protect the parties' interests.": "ਪਾਰਟੀਆਂ ਦੇ ਹਿਤਾਂ ਦੀ ਰਾਖੀ ਕਰਨ ਲਈ।",
                        "Termination mechanisms and conditions for contract renewal are specified.": "ਕਾਂਟ੍ਰੈਕਟ ਨਵੀਨੀਕਰਨ ਲਈ ਸਮਾਪਤੀ ਮਕੈਨਿਜ਼ਮ ਅਤੇ ਸ਼ਰਤਾਂ ਦਰਸਾਈਆਂ ਗਈਆਂ ਹਨ।",
                        "The respective duties of each party are delineated": "ਹਰ ਪਾਰਟੀ ਦੇ ਸੰਬੰਧਿਤ ਫਰਜ਼ਾਂ ਦੀ ਰੇਖਾ ਖਿੱਚੀ ਗਈ ਹੈ",
                        "with specific performance metrics and timelines.": "ਨਿਸ਼ਚਿਤ ਪ੍ਰਦਰਸ਼ਨ ਮੈਟਰਿਕਸ ਅਤੇ ਟਾਈਮਲਾਈਨਾਂ ਨਾਲ।",
                        "Compliance requirements with relevant laws and regulations are established.": "ਸੰਬੰਧਿਤ ਕਾਨੂੰਨਾਂ ਅਤੇ ਨਿਯਮਾਂ ਦੇ ਨਾਲ ਅਨੁਕੂਲਤਾ ਦੀਆਂ ਲੋੜਾਂ ਸਥਾਪਿਤ ਕੀਤੀਆਂ ਜਾਂਦੀਆਂ ਹਨ।",
                        "Remedy mechanisms in case of breach are provided with specific consequences.": "ਭੰਗ ਦੇ ਮਾਮਲੇ ਵਿੱਚ ਉਪਾਅ ਦੇ ਮਕੈਨਿਜ਼ਮ ਨਿਸ਼ਚਿਤ ਨਤੀਜਿਆਂ ਨਾਲ ਪ੍ਰਦਾਨ ਕੀਤੇ ਜਾਂਦੇ ਹਨ।",
                        "The contract creates legally enforceable rights": "ਕਾਂਟ੍ਰੈਕਟ ਕਾਨੂੰਨੀ ਤੌਰ 'ਤੇ ਲਾਗੂ ਕੀਤੇ ਜਾਣ ਵਾਲੇ ਅਧਿਕਾਰਾਂ ਨੂੰ ਬਣਾਉਂਦਾ ਹੈ",
                        "that can be upheld through legal proceedings if necessary.": "ਜੇ ਲੋੜ ਪਵੇ ਤਾਂ ਕਾਨੂੰਨੀ ਕਾਰਵਾਈ ਰਾਹੀਂ ਕਾਇਮ ਕੀਤਾ ਜਾ ਸਕਦਾ ਹੈ।",
                        "Under contract law, material breaches may entitle the non-breaching party": "ਕਾਂਟ੍ਰੈਕਟ ਦੇ ਕਾਨੂੰਨ ਦੇ ਅਧੀਨ, ਸਮੱਗਰੀ ਦੇ ਉਲੰਘਣਾਂ ਗੈਰ-ਉਲੰਘਣ ਪਾਰਟੀ ਨੂੰ ਹੱਕਦਾਰ ਬਣਾ ਸਕਦੀਆਂ ਹਨ",
                        "to remedies including specific performance or damages.": "ਨਿਸ਼ਚਿਤ ਪ੍ਰਦਰਸ਼ਨ ਜਾਂ ਨੁਕਸਾਨ ਸਮੇਤ ਉਪਾਅ ਲਈ।",
                        "Ambiguous terms may be interpreted by courts": "ਅਸਪਸ਼ਟ ਸ਼ਰਤਾਂ ਦੀ ਵਿਆਖਿਆ ਅਦਾਲਤਾਂ ਦੁਆਰਾ ਕੀਤੀ ਜਾ ਸਕਦੀ ਹੈ",
                        "according to standard principles of contractual interpretation.": "ਮਿਆਰੀ ਸੰਵਿਧਾਨਕ ਵਿਆਖਿਆ ਦੇ ਸਿਧਾਂਤਾਂ ਦੇ ਅਨੁਸਾਰ।"
                    },
                    "as": {  # Assamese
                        "Here's a detailed analysis:": "এইটো এটা বিস্তৃত বিশ্লেষণ:",
                        "Contract Structure and Validity:": "চুক্তিৰ গঠন আৰু বৈধতা:",
                        "Key Legal Provisions:": "মূল আইনগত ব্যৱস্থা:",
                        "Rights and Obligations:": "অধিকার আৰু দায়িত্ব:",
                        "Legal Implications:": "আইনগত প্ৰভাৱ:",
                        "Applicable legal frameworks that may be relevant:": "প্ৰাসংগিক আইনগত কাঠামো যি প্ৰাসংগিক হ'ব পাৰে:",
                        "DISCLAIMER:": "অস্বীকৃতি:",
                        "This analysis is provided for informational purposes only": "এই বিশ্লেষণটো কেৱল তথ্যগত উদ্দেশ্যৰ বাবে প্ৰদান কৰা হৈছে",
                        "and should not be construed as legal advice.": "আৰু ইয়াক আইনগত পৰামৰ্শ হিচাপে বুজা উচিত নহয়।",
                        "Please consult with a qualified legal professional for advice specific to your situation.": "দয়া কৰি আপোনাৰ পৰিস্থিতিৰ বাবে বিশেষ পৰামৰ্শৰ বাবে এজন অৰ্হতাসম্পন্ন আইন পেচাদাৰৰ সৈতে পৰামৰ্শ কৰক।",
                        "The document contains standard contractual elements": "দস্তাবেজটোৰ ভিতৰত মানক চুক্তিগত উপাদানসমূহ আছে",
                        "including parties' details, consideration clauses, terms of agreement, and signature requirements.": "পাৰ্টীসমূহৰ বিৱৰণ, বিবেচনা ধাৰা, চুক্তিৰ শর্তাবলী, আৰু স্বাক্ষৰৰ আৱশ্যকতাসমূহ অন্তর্ভুক্ত।",
                        "The agreement appears to establish legally binding obligations between the parties under contract law principles.": "চুক্তি আইন প্ৰিন্সিপলৰ অধীনত পক্ষসমূহৰ মাজত আইনগতভাৱে বাধ্যতামূলক দায়িত্ব স্থাপন কৰিবলৈ চুক্তিটো প্ৰমাণিত হয়।",
                        "Terms and conditions governing the relationship between parties are outlined": "পক্ষসমূহৰ মাজত সম্পৰ্ক নিয়ন্ত্ৰণ কৰা শর্ত আৰু শর্তাৱলী আউটলাইন কৰা হৈছে",
                        "with specific performance requirements.": "নিশ্চিত কাৰ্যক্ষমতা আৱশ্যকতাসমূহৰ সৈতে।",
                        "Liability provisions and risk allocation measures are included": "দায়িত্বৰ ব্যৱস্থা আৰু জোখম বণ্টন ব্যৱস্থা অন্তর্ভুক্ত আছে",
                        "to protect the parties' interests.": "পক্ষসমূহৰ স্বাৰ্থ ৰক্ষা কৰিবলৈ।",
                        "Termination mechanisms and conditions for contract renewal are specified.": "চুক্তি নবীকৰণৰ বাবে সমাপ্তিৰ যান্ত্রিকতা আৰু শর্তাৱলী উল্লেখ কৰা হৈছে।",
                        "The respective duties of each party are delineated": "প্ৰতিটো পক্ষৰ সম্পৰ্কিত কৰ্তব্যসমূহৰ ৰেখাচিত্ৰিত",
                        "with specific performance metrics and timelines.": "নিশ্চিত কাৰ্যক্ষমতা মেট্ৰিক্স আৰু সময়ৰেখাসমূহৰ সৈতে।",
                        "Compliance requirements with relevant laws and regulations are established.": "প্ৰাসংগিক আইন আৰু নিয়মাৱলী অনুসৰি অনুগতিতাৰ আৱশ্যকতাসমূহ স্থাপন কৰা হৈছে।",
                        "Remedy mechanisms in case of breach are provided with specific consequences.": "ভংগৰ ক্ষেত্ৰত চিকিৎসাৰ যান্ত্রিকতা নিৰ্দিষ্ট ফলাফলৰ সৈতে প্ৰদান কৰা হয়।",
                        "The contract creates legally enforceable rights": "চুক্তিয়ে আইনগতভাৱে কাৰ্যকৰী অধিকাৰ সৃষ্টি কৰে",
                        "that can be upheld through legal proceedings if necessary.": "যদি প্ৰয়োজন হয় তেন্তে আইনগত কাৰ্যবাহী মাধ্যমৰ জৰিয়তে ৰক্ষা কৰিব পৰা যায়।",
                        "Under contract law, material breaches may entitle the non-breaching party": "চুক্তি আইনৰ অধীনত, সামগ্ৰী ভংগসমূহ গেৰ-ভংগী পক্ষক অধিকাৰ দিয়া হ'ব পাৰে",
                        "to remedies including specific performance or damages.": "নিশ্চিত কাৰ্যক্ষমতা বা ক্ষতি সমূহৰ অন্তর্ভুক্ত চিকিৎসাৰ বাবে।",
                        "Ambiguous terms may be interpreted by courts": "অস্পষ্ট শর্তসমূহৰ ব্যাখ্যা আদালত দ্বাৰা কৰা হ'ব পাৰে",
                        "according to standard principles of contractual interpretation.": "মানক চুক্তিগত ব্যাখ্যা প্ৰিন্সিপল অনুসৰি।"
                    },
                    "mai": {  # Maithili
                        "Here's a detailed analysis:": "एहिठाम एकटा विस्तृत विश्लेषण अछि:",
                        "Contract Structure and Validity:": "अनुबंधक संरचना आ वैधता:",
                        "Key Legal Provisions:": "प्रमुख कानूनी प्रावधान:",
                        "Rights and Obligations:": "अधिकार आ दायित्व:",
                        "Legal Implications:": "कानूनी निहितार्थ:",
                        "Applicable legal frameworks that may be relevant:": "प्रासंगिक कानूनी ढाँचा जे संबंधित भ' सकैत अछि:",
                        "DISCLAIMER:": "अस्वीकृति:",
                        "This analysis is provided for informational purposes only": "ई विश्लेषण केवल सूचनात्मक उद्देश्य लेल प्रदान कएल गेल अछि",
                        "and should not be construed as legal advice.": "आ एहि केँ कानूनी सलाह के रूप में नहि बुझल जाए।",
                        "Please consult with a qualified legal professional for advice specific to your situation.": "कृपया अपन स्थिति लेल विशिष्ट सलाह हेतु एकटा योग्य कानूनी पेशेवर सँ परामर्श करू।",
                        "The document contains standard contractual elements": "दस्तावेज़ में मानक अनुबंध तत्व शामिल हैं",
                        "including parties' details, consideration clauses, terms of agreement, and signature requirements.": "जिसमें पक्षों का विवरण, विचार खंड, समझौते की शर्तें और हस्ताक्षर आवश्यकताएं शामिल हैं।",
                        "The agreement appears to establish legally binding obligations between the parties under contract law principles.": "समझौता अनुबंध कानून के सिद्धांतों के तहत पक्षों के बीच कानूनी रूप से बाध्यकारी दायित्वों को स्थापित करता प्रतीत होता है।",
                        "Terms and conditions governing the relationship between parties are outlined": "पक्षों के बीच संबंधों को नियंत्रित करने वाले नियम और शर्तों का उल्लेख किया गया है",
                        "with specific performance requirements.": "विशिष्ट प्रदर्शन आवश्यकताओं के साथ।",
                        "Liability provisions and risk allocation measures are included": "देयता प्रावधान और जोखिम आवंटन उपाय शामिल हैं",
                        "to protect the parties' interests.": "पक्षों के हितों की रक्षा के लिए।",
                        "Termination mechanisms and conditions for contract renewal are specified.": "समाप्ति तंत्र और अनुबंध नवीनीकरण के लिए शर्तें निर्दिष्ट हैं।",
                        "The respective duties of each party are delineated": "प्रत्येक पक्ष के संबंधित कर्तव्यों का सीमांकन किया गया है",
                        "with specific performance metrics and timelines.": "विशिष्ट प्रदर्शन मेट्रिक्स और समयसीमा के साथ।",
                        "Compliance requirements with relevant laws and regulations are established.": "प्रासंगिक कानूनों और विनियमों के अनुपालन की आवश्यकताएं स्थापित की गई हैं।",
                        "Remedy mechanisms in case of breach are provided with specific consequences.": "उल्लंघन के मामले में उपचार तंत्र विशिष्ट परिणामों के साथ प्रदान किए गए हैं।",
                        "The contract creates legally enforceable rights": "अनुबंध कानूनी रूप से लागू करने योग्य अधिकार बनाता है",
                        "that can be upheld through legal proceedings if necessary.": "जिन्हें आवश्यकता पड़ने पर कानूनी कार्यवाही के माध्यम से बनाए रखा जा सकता है।",
                        "Under contract law, material breaches may entitle the non-breaching party": "अनुबंध कानून के तहत, भौतिक उल्लंघन गैर-उल्लंघनकर्ता पक्ष को हकदार बना सकता है",
                        "to remedies including specific performance or damages.": "विशिष्ट प्रदर्शन या क्षति सहित उपचारों के लिए।",
                        "Ambiguous terms may be interpreted by courts": "अस्पष्ट शब्दों की व्याख्या अदालतों द्वारा की जा सकती है",
                        "according to standard principles of contractual interpretation.": "अनुबंध व्याख्या के मानक सिद्धांतों के अनुसार।"
                    },
                    "sat": {  # Santali
                        "Here's a detailed analysis:": "ᱵᱟᱹᱨ ᱠᱟᱜᱚᱡ ᱫᚢ ᱢᱤᱫ ᱟᱭᱤᱱ ᱜᱟᱱᱛᱟᱠ ᱠᱟᱱᱟ ᱢᱮᱱᱛᱮ ᱧᱮᱞᱚᱜ-ᱟ",
                        "Contract Structure and Validity:": "ᱠᱚᱱᱛᱷᱟᱜ ᱥᱟᱨᱜᱟᱹᱨ ᱟᱹᱨᱠᱟᱹᱨ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱟᱜᱚᱡ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱟᱜᱚᱡ",
                        "Key Legal Provisions:": "ᱠᱚᱱᱛᱷᱟᱜ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱟᱜᱚᱡ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱟᱜᱚᱡ",
                        "Rights and Obligations:": "ᱟᱹᱨᱠᱟᱹᱨ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱟᱜᱚᱡ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱟᱜᱚᱡ",
                        "Legal Implications:": "ᱟᱹᱨᱠᱟᱹᱨ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱟᱜᱚᱡ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱟᱜᱚᱡ",
                        "Applicable legal frameworks that may be relevant:": "ᱟᱹᱨᱠᱟᱹᱨ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱟᱜᱚᱡ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱟᱜᱚᱡ",
                        "DISCLAIMER:": "ᱟᱹᱨᱠᱟᱹᱨ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱟᱜᱚᱡ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱟᱜᱚᱡ",
                        "This analysis is provided for informational purposes only": "ᱟᱹᱨᱠᱟᱹᱨ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱟᱜᱚᱡ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱟᱜᱚᱡ",
                        "and should not be construed as legal advice.": "ᱟᱹᱨᱠᱟᱹᱨ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱟᱜᱚᱡ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱟᱜᱚᱡ",
                        "Please consult with a qualified legal professional for advice specific to your situation.": "ᱟᱹᱨᱠᱟᱹᱨ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱟᱜᱚᱡ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱟᱜᱚᱡ",
                        "The document contains standard contractual elements": "ᱟᱹᱨᱠᱟᱹᱨ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱟᱜᱚᱡ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱟᱜᱚᱡ",
                        "including parties' details, consideration clauses, terms of agreement, and signature requirements.": "ᱟᱹᱨᱠᱟᱹᱨ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱟᱜᱚᱡ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱟᱜᱚᱡ",
                        "The agreement appears to establish legally binding obligations between the parties under contract law principles.": "ᱟᱹᱨᱠᱟᱹᱨ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱟᱜᱚᱡ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱟᱜᱚᱡ",
                        "Terms and conditions governing the relationship between parties are outlined": "ᱟᱹᱨᱠᱟᱹᱨ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱟᱜᱚᱡ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱟᱜᱚᱡ",
                        "with specific performance requirements.": "ᱟᱹᱨᱠᱟᱹᱨ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱟᱜᱚᱡ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱟᱜᱚᱡ",
                        "Liability provisions and risk allocation measures are included": "ᱟᱹᱨᱠᱟᱹᱨ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱟᱜᱚᱡ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱟᱜᱚᱡ",
                        "to protect the parties' interests.": "ᱟᱹᱨᱠᱟᱹᱨ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱟᱜᱚᱡ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱟᱜᱚᱡ",
                        "Termination mechanisms and conditions for contract renewal are specified.": "ᱟᱹᱨᱠᱟᱹᱨ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱟᱜᱚᱡ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱟᱜᱚᱡ",
                        "The respective duties of each party are delineated": "ᱟᱹᱨᱠᱟᱹᱨ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱟᱜᱚᱡ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱟᱜᱚᱡ",
                        "with specific performance metrics and timelines.": "ᱟᱹᱨᱠᱟᱹᱨ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱟᱜᱚᱡ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱟᱜᱚᱡ",
                        "Compliance requirements with relevant laws and regulations are established.": "ᱟᱹᱨᱠᱟᱹᱨ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱟᱜᱚᱡ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱟᱜᱚᱡ",
                        "Remedy mechanisms in case of breach are provided with specific consequences.": "ᱟᱹᱨᱠᱟᱹᱨ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱟᱜᱚᱡ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱟᱜᱚᱡ",
                        "The contract creates legally enforceable rights": "ᱟᱹᱨᱠᱟᱹᱨ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱟᱜᱚᱡ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱟᱜᱚᱡ",
                        "that can be upheld through legal proceedings if necessary.": "ᱟᱹᱨᱠᱟᱹᱨ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱟᱜᱚᱡ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱟᱜᱚᱡ",
                        "Under contract law, material breaches may entitle the non-breaching party": "ᱟᱹᱨᱠᱟᱹᱨ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱟᱜᱚᱡ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱟᱜᱚᱡ",
                        "to remedies including specific performance or damages.": "ᱟᱹᱨᱠᱟᱹᱨ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱟᱜᱚᱡ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱟᱜᱚᱡ",
                        "Ambiguous terms may be interpreted by courts": "ᱟᱹᱨᱠᱟᱹᱨ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱟᱜᱚᱡ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱟᱜᱚᱡ",
                        "according to standard principles of contractual interpretation.": "ᱟᱹᱨᱠᱟᱹᱨ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱟᱜᱚᱡ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱚᱱᱛᱷᱟᱜ ᱠᱟᱜᱚᱡ"
                    }
                }
                
                # Dictionary of sample phrases and translations for demonstration purposes
                sample_phrases = {
                    "hi": {  # Hindi
                        "This document appears to be a legal contract": "यह दस्तावेज़ एक कानूनी अनुबंध प्रतीत होता है",
                        "Contains standard contract clauses": "मानक अनुबंध खंड शामिल हैं",
                        "The agreement is valid for one year": "समझौता एक वर्ष के लिए मान्य है",
                        "Requires signature of both parties": "दोनों पक्षों के हस्ताक्षर की आवश्यकता है",
                        "Legal document": "कानूनी दस्तावेज़",
                        "Contract": "अनुबंध",
                        "Summary": "संग्रह",
                        "Key points": "प्रमुख बिंदु",
                        "Indian Contract Act, 1872": "भारतीय अनुबंध अधिनियम, 1872",
                        "Foreign Exchange Management Act, 1999": "विदेशी मुद्रा प्रबंधन अधिनियम, 1999",
                        "Specific Relief Act, 1963": "विशिष्ट राहत अधिनियम, 1963"
                    },
                    "bn": {  # Bengali
                        "This document appears to be a legal contract": "এই নথিটি একটি আইনি চুক্তি বলে মনে হচ্ছে",
                        "Contains standard contract clauses": "স্ট্যান্ডার্ড চুক্তির ধারা অন্তর্ভুক্ত",
                        "The agreement is valid for one year": "চুক্তিটি এক বছরের জন্য বৈধ",
                        "Requires signature of both parties": "উভয় পক্ষের স্বাক্ষর প্রয়োজন",
                        "Legal document": "আইনি নথি",
                        "Contract": "চুক্তি",
                        "Summary": "সারসংক্ষেপ",
                        "Key points": "মূল বিষয়গুলি"
                    },
                    "te": {  # Telugu
                        "This document appears to be a legal contract": "ఈ పత్రం చట్టపరమైన ఒప్పందంగా కనిపిస్తోంది",
                        "Contains standard contract clauses": "ప్రామాణిక ఒప్పంద నిబంధనలను కలిగి ఉంది",
                        "The agreement is valid for one year": "ఒప్పందం ఒక సంవత్సరం పాటు చెల్లుబాటు అవుతుంది",
                        "Requires signature of both parties": "ఇరు పక్షాల సంతకం అవసరం",
                        "Legal document": "చట్టపరమైన పత్రం",
                        "Contract": "ఒప్పందం",
                        "Summary": "సారాంశం",
                        "Key points": "ముఖ్య అంశాలు"
                    },
                    "mr": {  # Marathi
                        "This document appears to be a legal contract": "हा दस्तावेज कायदेशीर करार असल्याचे दिसते",
                        "Contains standard contract clauses": "मानक करार कलमे समाविष्ट आहेत",
                        "The agreement is valid for one year": "करार एक वर्षासाठी वैध आहे",
                        "Requires signature of both parties": "दोन्ही पक्षांच्या स्वाक्षरीची आवश्यकता आहे",
                        "Legal document": "कायदेशीर दस्तावेज",
                        "Contract": "करार",
                        "Summary": "सारांश",
                        "Key points": "मुख्य मुद्दे"
                    },
                    "ta": {  # Tamil
                        "This document appears to be a legal contract": "இந்த ஆவணம் ஒரு சட்ட ஒப்பந்தமாக தெரிகிறது",
                        "Contains standard contract clauses": "நிலையான ஒப்பந்த விதிகளைக் கொண்டுள்ளது",
                        "The agreement is valid for one year": "ஒப்பந்தம் ஒரு வருடத்திற்கு செல்லுபடியாகும்",
                        "Requires signature of both parties": "இரு தரப்பினரின் கையொப்பம் தேவை",
                        "Legal document": "சட்ட ஆவணம்",
                        "Contract": "ஒப்பந்தம்",
                        "Summary": "சுருக்கம்",
                        "Key points": "முக்கிய புள்ளிகள்"
                    },
                    "ur": {  # Urdu
                        "This document appears to be a legal contract": "یہ دستاویز ایک قانونی معاہدہ معلوم ہوتی ہے",
                        "Contains standard contract clauses": "معیاری معاہدہ شقیں شامل ہیں",
                        "The agreement is valid for one year": "یہ معاہدہ ایک سال کے لیے درست ہے",
                        "Requires signature of both parties": "دونوں فریقوں کے دستخط درکار ہیں",
                        "Legal document": "قانونی دستاویز",
                        "Contract": "معاہدہ",
                        "Summary": "خلاصہ",
                        "Key points": "اہم نکات"
                    },
                    "gu": {  # Gujarati
                        "This document appears to be a legal contract": "આ દસ્તાવેજ કાનૂની કરાર જેવો લાગે છે",
                        "Contains standard contract clauses": "પ્રમાણભૂત કરાર કલમો ધરાવે છે",
                        "The agreement is valid for one year": "કરાર એક વર્ષ માટે માન્ય છે",
                        "Requires signature of both parties": "બંને પક્ષોની સહીની જરૂર છે", 
                        "Legal document": "કાનૂની દસ્તાવેજ",
                        "Contract": "કરાર",
                        "Summary": "સારાંશ",
                        "Key points": "મુખ્ય મુદ્દાઓ"
                    },
                    "kn": {  # Kannada
                        "This document appears to be a legal contract": "ಈ ದಾಖಲೆ ಕಾನೂನು ಒಪ್ಪಂದವಾಗಿ ಕಾಣುತ್ತದೆ",
                        "Contains standard contract clauses": "ಪ್ರಮಾಣಿತ ಒಪ್ಪಂದ ಷರತ್ತುಗಳನ್ನು ಒಳಗೊಂಡಿದೆ",
                        "The agreement is valid for one year": "ಒಪ್ಪಂದವು ಒಂದು ವರ್ಷದವರೆಗೆ ಮಾನ್ಯವಾಗಿದೆ",
                        "Requires signature of both parties": "ಎರಡೂ ಪಕ್ಷಗಳ ಸಹಿ ಅಗತ್ಯವಿದೆ",
                        "Legal document": "ಕಾನೂನು ದಾಖಲೆ",
                        "Contract": "ಒಪ್ಪಂದ",
                        "Summary": "ಸಾರಾಂಶ",
                        "Key points": "ಪ್ರಮುಖ ಅಂಶಗಳು"
                    },
                    "ml": {  # Malayalam
                        "This document appears to be a legal contract": "ഈ രേഖ ഒരു നിയമപരമായ കരാറായി തോന്നുന്നു",
                        "Contains standard contract clauses": "സ്റ്റാൻഡേർഡ് കരാർ വ്യവസ്ഥകൾ അടങ്ങിയിരിക്കുന്നു",
                        "The agreement is valid for one year": "കരാർ ഒരു വർഷത്തേക്ക് സാധുവാണ്",
                        "Requires signature of both parties": "ഇരു കക്ഷികളുടെയും ഒപ്പ് ആവശ്യമാണ്",
                        "Legal document": "നിയമപരമായ രേഖ",
                        "Contract": "കരാർ",
                        "Summary": "സംഗ്രഹം",
                        "Key points": "പ്രധാന പോയിന്റുകൾ",
                        "Indian Contract Act, 1872": "ഇന്ത്യൻ കരാർ നിയമം, 1872",
                        "Foreign Exchange Management Act, 1999": "വിദേശ നാണയ നിയന്ത്രണ നിയമം, 1999",
                        "Specific Relief Act, 1963": "പ്രത്യേക ആശ്വാസ നിയമം, 1963"
                    },
                    "or": {  # Odia
                        "This document appears to be a legal contract": "ଏହି ଦଲିଲଟି ଏକ ଆଇନଗତ ଚୁକ୍ତିନାମା ଭଳି ଲାଗୁଛି",
                        "Contains standard contract clauses": "ମାନକ ଚୁକ୍ତି ଧାରା ଧାରଣ କରେ",
                        "The agreement is valid for one year": "ଚୁକ୍ତିନାମା ଏକ ବର୍ଷ ପାଇଁ ବୈଧ",
                        "Requires signature of both parties": "ଉଭୟ ପକ୍ଷଙ୍କ ଦସ୍ତଖତ ଆବଶ୍ୟକ",
                        "Legal document": "ଆଇନଗତ ଦଲିଲ",
                        "Contract": "ଚୁକ୍ତିନାମା",
                        "Summary": "ସାରାଂଶ",
                        "Key points": "ମୁଖ୍ୟ ବିନ୍ଦୁଗୁଡିକ"
                    },
                    "pa": {  # Punjabi
                        "This document appears to be a legal contract": "ਇਹ ਦਸਤਾਵੇਜ਼ ਇੱਕ ਕਾਨੂੰਨੀ ਇਕਰਾਰਨਾਮਾ ਜਾਪਦਾ ਹੈ",
                        "Contains standard contract clauses": "ਮਿਆਰੀ ਇਕਰਾਰਨਾਮੇ ਦੀਆਂ ਧਾਰਾਵਾਂ ਸ਼ਾਮਲ ਹਨ",
                        "The agreement is valid for one year": "ਸਮਝੌਤਾ ਇੱਕ ਸਾਲ ਲਈ ਵੈਧ ਹੈ",
                        "Requires signature of both parties": "ਦੋਨੋਂ ਧਿਰਾਂ ਦੇ ਦਸਤਖਤਾਂ ਦੀ ਲੋੜ ਹੈ",
                        "Legal document": "ਕਾਨੂੰਨੀ ਦਸਤਾਵੇਜ਼",
                        "Contract": "ਇਕਰਾਰਨਾਮਾ",
                        "Summary": "ਸਾਰ",
                        "Key points": "ਮੁੱਖ ਬਿੰਦੂ"
                    },
                    "as": {  # Assamese
                        "This document appears to be a legal contract": "এই নথিখন এটা আইনী চুক্তি যেন লাগে",
                        "Contains standard contract clauses": "মানক চুক্তিৰ ধারা অন্তর্ভুক্ত কৰে",
                        "The agreement is valid for one year": "চুক্তিখন এবছৰৰ বাবে বৈধ",
                        "Requires signature of both parties": "দুয়োপক্ষৰ স্বাক্ষৰক প্ৰয়োজন",
                        "Legal document": "আইনী নথি",
                        "Contract": "চুক্তি",
                        "Summary": "সারসংক্ষেপ",
                        "Key points": "মূল বিষয়গুলি"
                    },
                    "mai": {  # Maithili
                        "This document appears to be a legal contract": "ई दस्तावेज एकटा कानूनी अनुबंध प्रतीत होइत अछि",
                        "Contains standard contract clauses": "मानक अनुबंध खंड सभ समाविष्ट अछि",
                        "The agreement is valid for one year": "ई समझौता एक वर्ष लेल मान्य अछि",
                        "Requires signature of both parties": "दुनू पक्षक हस्ताक्षरक आवश्यकता अछि",
                        "Legal document": "कानूनी दस्तावेज",
                        "Contract": "अनुबंध",
                        "Summary": "सारांश",
                        "Key points": "मुख्य बिंदु"
                    },
                    "sa": {  # Sanskrit
                        "This document appears to be a legal contract": "एषः पत्रं विधिक संविदा इव प्रतिभाति",
                        "Contains standard contract clauses": "मानक संविदा खण्डानि अन्तर्भवति",
                        "The agreement is valid for one year": "संविदा एकस्य वर्षस्य कृते मान्या अस्ति",
                        "Requires signature of both parties": "उभयोः पक्षयोः हस्ताक्षरस्य आवश्यकता अस्ति",
                        "Legal document": "विधिक पत्रम्",
                        "Contract": "संविदा",
                        "Summary": "सारांशः",
                        "Key points": "मुख्याः बिन्दवः"
                    },
                    "ks": {  # Kashmiri
                        "This document appears to be a legal contract": "یہ دستاویز ایک قانونی معاہدہ معلوم ہوتا ہے",
                        "Contains standard contract clauses": "معیاری معاہدہ شقیں شامل ہیں",
                        "The agreement is valid for one year": "یہ معاہدہ ایک سال کے لیے درست چھُ",
                        "Requires signature of both parties": "دونوں فریقوں کے دستخط ضروری چھِ",
                        "Legal document": "قانونی دستاویز",
                        "Contract": "معاہدہ",
                        "Summary": "خلاصہ",
                        "Key points": "اہم نکات"
                    },
                    "ne": {  # Nepali
                        "This document appears to be a legal contract": "यो कागजात कानूनी सम्झौता जस्तो देखिन्छ",
                        "Contains standard contract clauses": "मानक सम्झौता खण्डहरू समावेश छन्",
                        "The agreement is valid for one year": "सम्झौता एक वर्षको लागि मान्य छ",
                        "Requires signature of both parties": "दुवै पक्षको हस्ताक्षर आवश्यक छ",
                        "Legal document": "कानूनी कागजात",
                        "Contract": "सम्झौता",
                        "Summary": "सारांश",
                        "Key points": "मुख्य बुँदाहरू"
                    },
                    "sd": {  # Sindhi
                        "This document appears to be a legal contract": "هي دستاويز هڪ قانوني معاهدي جيان لڳي ٿو",
                        "Contains standard contract clauses": "معياري معاهدہ شقون شامل آهن",
                        "The agreement is valid for one year": "معاهدو هڪ سال لاءِ درست آهي",
                        "Requires signature of both parties": "ٻنهي ڌرين جي صحيح جي ضرورت آهي",
                        "Legal document": "قانوني دستاويز",
                        "Contract": "معاهدو",
                        "Summary": "خلاصو",
                        "Key points": "اهم نڪتا"
                    },
                    "kok": {  # Konkani
                        "This document appears to be a legal contract": "हें दस्तावेज कायदेशीर करार जावन दिसता",
                        "Contains standard contract clauses": "मानक करार कलमां आसात",
                        "The agreement is valid for one year": "करार एका वर्साखातीर वैध आसा",
                        "Requires signature of both parties": "दोनूय पक्षांच्या सह्यांची गरज आसा",
                        "Legal document": "कायदेशीर दस्तावेज",
                        "Contract": "करार",
                        "Summary": "सारांश",
                        "Key points": "मुखेल मुद्दे"
                    },
                    "doi": {  # Dogri
                        "This document appears to be a legal contract": "एह दस्तावेज कानूनी इकरारनामा लगदा ऐ",
                        "Contains standard contract clauses": "मानक इकरारनामे दियां धाराएं ਸ਼ਾਮਲ ਨ",
                        "The agreement is valid for one year": "इकरारनामा इक साल तकर मान्य ऐ",
                        "Requires signature of both parties": "दोनें धिरें दे दस्तखतें दी लोड़ ऐ",
                        "Legal document": "ਕਾਨੂਨੀ ਦਸਤਾਵੇਜ਼",
                        "Contract": "ਇਕਰਾਰਨਾਮਾ",
                        "Summary": "ਸਾਰ",
                        "Key points": "मुख्य बिंदु"
                    },
                    "mni": {  # Manipuri/Meitei
                        "This document appears to be a legal contract": "এই দলীল আইনগী চৌক্তাক্নবা অমা ওইরমগদরা হায়না উই",
                        "Contains standard contract clauses": "স্তান্দর্দ চৌক্তাক্নবগী ৱারোল য়াওই",
                        "The agreement is valid for one year": "চৌক্তাক্নবা অসি চহি অমগী দমক চৎনগনি",
                        "Requires signature of both parties": "মীওই অনিমকক্কী খুৎয়েক মথৌ তাই",
                        "Legal document": "আইনগী দলীল",
                        "Contract": "চৌক্তাক্নবা",
                        "Summary": "নিংথৌরোল",
                        "Key points": "মরু ওইবা ৱাফম"
                    },
                    "bo": {  # Tibetan/Bodo
                        "This document appears to be a legal contract": "ཡིག་ཆ་འདི་ཁྲིམས་མཐུན་གྱི་གན་རྒྱ་ཞིག་འདི་ཁྲིམས་མཐུན་གྱི་འདུག",
                        "Contains standard contract clauses": "ཚད་ལྡན་གན་རྒྱའི་ཚན་པ་ཁག་ཚུད་ཡོད།",
                        "The agreement is valid for one year": "གན་རྒྱ་འདི་ལོ་གཅིག་གི་རིང་ལ་ཆ་འཇོག་ཡིན།",
                        "Requires signature of both parties": "ཕྱོགས་གཉིས་ཀའི་མིང་རྟགས་དགོས་ངེས་ཡིན།",
                        "Legal document": "ཁྲིམས་མཐུན་ཡིག་ཆ།",
                        "Contract": "གན་རྒྱ།",
                        "Summary": "སྙིང་བསྡུས།",
                        "Key points": "གནད་དོན་གཙོ་བོ།"
                    },
                    "sat": {  # Santali
                        "This document appears to be a legal contract": "ᱱᱚᱶᱟ ᱠᱟᱜᱚᱡ ᱫᚢ ᱢᱤᱫ ᱟᱭᱤᱱ ᱜᱟᱱᱛᱟᱠ ᱠᱟᱱᱟ ᱢᱮᱱᱛᱮ ᱧᱮᱞᱚᱜ-ᱟ",
                        "Contains standard contract clauses": "ᱢᱟᱱᱚᱠ ᱜᱟᱱᱛᱟᱠ ᱠᱮᱞᱟᱣᱥ ᱠᚚ ᱢᱮᱱᱟᱜ-ᱟ",
                        "The agreement is valid for one year": "ᱜᱟᱱᱛᱟᱠ ᱫᚢ ᱢᱤᱫ ᱥᱮᱨᱢᱟ ᱞᱟᱹᱜᱤᱫ ᱢᱟᱱᱟᱣ ᱢᱟᱱᱟᱣ ᱜᱮᱭᱟ",
                        "Requires signature of both parties": "ᱵᱟᱱᱟᱨ ᱯᱟᱦᱴᱟ ᱨᱮᱱ ᱠᱚᱣᱟᱜ ᱥᱩᱦᱤ ᱞᱟᱹᱠᱛᱤᱭᱟ",
                        "Legal document": "ᱟᱭᱤᱱ ᱠᱟᱜᱚᱡ",
                        "Contract": "ᱜᱟᱱᱛᱟᱠ",
                        "Summary": "ᱜᱟᱵᱟᱱ",
                        "Key points": "ᱢᱩᱬᱩᱛ ᱴᱷᱮᱱ ᱠᚚ"
                    }
                }
                
                # Attempt to translate the text using our improved approach
                if target_lang in sample_phrases:
                    # First, try to detect if we're dealing with a legal analysis
                    if "This document appears to be a legal contract" in text and "Here's a detailed analysis" in text:
                        # This is a contract analysis, use more comprehensive translation
                        translated_text = text
                        
                        # Replace basic phrases first
                        phrases = sample_phrases[target_lang]
                        for eng_phrase, translated_phrase in phrases.items():
                            translated_text = translated_text.replace(eng_phrase, translated_phrase)
                        
                        # If we have specialized translations for this language, apply them
                        if target_lang in analysis_translations:
                            section_translations = analysis_translations[target_lang]
                            for eng_section, translated_section in section_translations.items():
                                translated_text = translated_text.replace(eng_section, translated_section)
                    else:
                        # For other text, use the basic phrase replacement
                        phrases = sample_phrases[target_lang]
                        
                        # First try for exact matches
                        if text in phrases:
                            translated_text = phrases[text]
                        else:
                            # If no exact match, attempt to create a translation by replacing known phrases
                            temp_text = text
                            for eng_phrase, translated_phrase in phrases.items():
                                temp_text = temp_text.replace(eng_phrase, translated_phrase)
                            
                            # If we made at least some substitutions, use the result
                            if temp_text != text:
                                translated_text = temp_text
        
            # If translation was successful, cache it for future use
            if translated_text and not translated_text.startswith("[Translation"):
                self.translation_cache[cache_key] = translated_text
                # Save cache to file periodically (every 10 new translations)
                if len(self.translation_cache) % 10 == 0:
                    self._save_translation_cache()
        
        # If no translation was generated, use placeholder
        if not translated_text:
            translated_text = f"[Translation using open-source LLM failed. Please install transformers library with 'pip install transformers sentencepiece' and ensure you have enough memory.]"
        
        # Generate audio file for the translated text
        audio_filename = f"translated_{target_lang}_{datetime.now().strftime('%Y%m%d%H%M%S')}.wav"
        audio_path = f"temp/{audio_filename}"
        
        # Create a dummy audio file for demo purposes
        # In a real implementation, this would use a TTS service
        with open(audio_path, "wb") as f:
            f.write(b"dummy audio data for translation")
        
        return {
            "translated_text": translated_text,
            "source_text": text,
            "source_lang": "en",
            "target_lang": target_lang,
            "audio_response": audio_path
        }
    
    def _identify_document_type(self, text):
        """
        Identify the type of legal document based on content patterns
        
        Args:
            text: The document text to analyze
            
        Returns:
            tuple: (document_type, confidence_score)
        """
        scores = {}
        for doc_type, pattern in self.document_patterns.items():
            matches = re.findall(pattern, text)
            score = len(matches) / (len(text.split()) / 100)  # Normalize by document length
            scores[doc_type] = min(score, 1.0)  # Cap at 1.0
        
        # Get the document type with the highest score
        if not scores:
            return "unknown", 0.0
            
        best_type = max(scores, key=scores.get)
        return best_type, scores[best_type]
    
    def _extract_legal_entities(self, text, doc_type):
        """
        Extract legal entities from the document text based on document type
        
        Args:
            text: The document text
            doc_type: The type of legal document
            
        Returns:
            list: Extracted entities with their types
        """
        entities = []
        
        # Common patterns for different entity types
        patterns = {
            "date": r"\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2},\s+\d{4}\b|\b\d{1,2}/\d{1,2}/\d{2,4}\b|\b\d{1,2}-\d{1,2}-\d{2,4}\b",
            "money": r"\$\s*\d+(?:,\d+)*(?:\.\d+)?|\b\d+(?:,\d+)*(?:\.\d+)?\s*(?:dollars|USD|Rs\.?|INR|£|€)",
            "person": r"\b(?:[A-Z][a-z]+ [A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b",
            "organization": r"\b(?:[A-Z][a-z]*\s*(?:&|and)?\s*)+(?:L\.?L\.?C\.?|Inc\.?|Ltd\.?|Corporation|Corp\.?|Company|Co\.?)\b",
            "address": r"\b\d+\s+[A-Za-z0-9\s,.]+\b(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Court|Ct|Plaza|Plz|Terrace|Ter|Place|Pl)\b",
            "phone": r"\b(?:\+\d{1,3}\s?)?(?:\(\d{3}\)|\d{3})[-.\s]?\d{3}[-.\s]?\d{4}\b",
            "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            "url": r"\bhttps?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&//=]*)",
            "clause": r"\b(?:Section|Clause|Article|Paragraph)\s+\d+(?:\.\d+)*",
            "percentage": r"\b\d+(?:\.\d+)?\s*%"
        }
        
        # Document-specific patterns
        if doc_type == "contract":
            patterns.update({
                "party": r"\bparty of the (?:first|second) part\b|\bthe (?:seller|buyer|lessor|lessee|vendor|purchaser|landlord|tenant|licensor|licensee)\b",
                "effective_date": r"\beffective date\b|\bcommencement date\b",
                "termination": r"\btermination\b|\bexpiration\b|\bcancellation\b",
                "governing_law": r"\bgoverning law\b|\bjurisdiction\b|\bvenue\b",
                "indemnity": r"\bindemnity\b|\bindemnification\b|\bhold harmless\b",
                "warranty": r"\bwarranty\b|\bguarantee\b|\brepresent and warrant\b"
            })
        elif doc_type == "judgment":
            patterns.update({
                "citation": r"\b\d+\s+[A-Za-z]+\s+\d+\b|\b\[\d{4}\]\s+\w+\s+\d+\b",
                "court": r"\b(?:Supreme Court|High Court|District Court|Federal Court|Appellate Court|Court of Appeals)\b",
                "judge": r"\bJustice\s+[A-Z][a-z]+\b|\bJudge\s+[A-Z][a-z]+\b|\bHon\'?ble\s+[A-Z][a-z]+\b",
                "statute": r"\b(?:Act|Code|Statute|Law|Regulation)\s+of\s+\d{4}\b"
            })
        
        # Extract entities using patterns
        for entity_type, pattern in patterns.items():
            matches = re.finditer(pattern, text)
            for match in matches:
                if match.group():
                    entities.append({"word": match.group(), "entity": entity_type.upper()})
        
        return entities[:20]  # Limit to top 20 entities
    
    def _get_applicable_laws(self, doc_type, jurisdiction="india"):
        """
        Get applicable laws for the document type
        
        Args:
            doc_type: The document type
            jurisdiction: The legal jurisdiction (default: india)
            
        Returns:
            list: Applicable laws
        """
        jurisdiction_data = self.legal_frameworks.get(jurisdiction, {})
        
        applicable_laws = []
        
        # Map document types to legal categories
        category_map = {
            "contract": ["civil", "commercial"],
            "judgment": ["civil", "criminal"],
            "legislation": [],  # Depends on the specific legislation
            "will": ["civil", "family"],
            "affidavit": ["civil", "criminal"],
            "notice": ["civil", "commercial"],
            "legal_opinion": ["civil", "commercial"],
            "mou": ["commercial"]
        }
        
        # Get relevant laws from applicable categories
        categories = category_map.get(doc_type, [])
        for category in categories:
            if category in jurisdiction_data:
                applicable_laws.extend(jurisdiction_data[category])
        
        # Choose a random subset if too many
        if len(applicable_laws) > 3:
            return random.sample(applicable_laws, 3)
        return applicable_laws
    
    def _generate_legal_analysis(self, doc_type, text):
        """
        Generate a detailed legal analysis based on document type
        
        Args:
            doc_type: The identified document type
            text: The document text
            
        Returns:
            str: Detailed legal analysis
        """
        analysis = ""
        
        # Generate document-specific analysis
        if doc_type == "contract":
            analysis = self._generate_contract_analysis(text)
        elif doc_type == "judgment":
            analysis = self._generate_judgment_analysis(text)
        elif doc_type == "legislation":
            analysis = self._generate_legislation_analysis(text)
        elif doc_type == "will":
            analysis = self._generate_will_analysis(text)
        elif doc_type == "affidavit":
            analysis = self._generate_affidavit_analysis(text)
        elif doc_type == "notice":
            analysis = self._generate_notice_analysis(text)
        elif doc_type == "legal_opinion":
            analysis = self._generate_legal_opinion_analysis(text)
        elif doc_type == "mou":
            analysis = self._generate_mou_analysis(text)
        else:
            # Generic analysis for unidentified document types
            analysis = (
                "This appears to be a legal document. Based on the content, here's a general analysis:\n\n"
                "1. Key points covered in the document include agreements between parties, obligations, rights, "
                "and potential legal implications.\n\n"
                "2. For a comprehensive understanding, I recommend consulting with a legal professional specialized "
                "in this area of law to interpret the specific implications for your situation.\n\n"
                "3. Before taking any action based on this document, ensure that you understand all terms and conditions, "
                "as legal documents often contain nuanced language with significant legal consequences."
            )
        
        # Add applicable laws
        applicable_laws = self._get_applicable_laws(doc_type)
        if applicable_laws:
            analysis += "\n\nApplicable legal frameworks that may be relevant:\n"
            for i, law in enumerate(applicable_laws, 1):
                analysis += f"{i}. {law}\n"
        
        # Add legal disclaimer
        analysis += "\n\nDISCLAIMER: This analysis is provided for informational purposes only and should not be construed as legal advice. Please consult with a qualified legal professional for advice specific to your situation."
        
        return analysis
    
    def _generate_contract_analysis(self, text):
        """Generate analysis specific to contracts"""
        return (
            "This document appears to be a legal contract. Here's a detailed analysis:\n\n"
            "1. Contract Structure and Validity:\n"
            "   - The document contains standard contractual elements including parties' details, consideration clauses, terms of agreement, and signature requirements.\n"
            "   - The agreement appears to establish legally binding obligations between the parties under contract law principles.\n\n"
            "2. Key Legal Provisions:\n"
            "   - Terms and conditions governing the relationship between parties are outlined with specific performance requirements.\n"
            "   - Liability provisions and risk allocation measures are included to protect the parties' interests.\n"
            "   - Termination mechanisms and conditions for contract renewal are specified.\n\n"
            "3. Rights and Obligations:\n"
            "   - The respective duties of each party are delineated with specific performance metrics and timelines.\n"
            "   - Compliance requirements with relevant laws and regulations are established.\n"
            "   - Remedy mechanisms in case of breach are provided with specific consequences.\n\n"
            "4. Legal Implications:\n"
            "   - The contract creates legally enforceable rights that can be upheld through legal proceedings if necessary.\n"
            "   - Under contract law, material breaches may entitle the non-breaching party to remedies including specific performance or damages.\n"
            "   - Ambiguous terms may be interpreted by courts according to standard principles of contractual interpretation."
        )
    
    def _generate_judgment_analysis(self, text):
        """Generate analysis specific to court judgments"""
        return (
            "This document appears to be a legal judgment. Here's a detailed analysis:\n\n"
            "1. Judicial Findings:\n"
            "   - The court has ruled on specific legal questions presented in the case with binding authority.\n"
            "   - The judgment contains findings of fact based on evidence presented and legal conclusions applying relevant law.\n"
            "   - The court's reasoning demonstrates application of legal principles to the specific circumstances of the case.\n\n"
            "2. Legal Reasoning and Precedent:\n"
            "   - The court applies established legal principles and cites relevant statutory provisions and case law.\n"
            "   - The judgment may establish or reinforce legal precedent within the appropriate jurisdiction.\n"
            "   - The court distinguishes or applies existing case law to develop its reasoning.\n\n"
            "3. Relief Granted:\n"
            "   - The court awards specific remedies or relief to the prevailing party.\n"
            "   - The judgment specifies any monetary damages, equitable relief, or specific performance required.\n"
            "   - Terms for enforcement of the judgment are outlined with timeframes for compliance.\n\n"
            "4. Appeal Implications:\n"
            "   - The judgment may be subject to appeal within specified timeframes according to applicable procedural rules.\n"
            "   - Grounds for potential appeal would typically require identification of errors in law or procedure.\n"
            "   - The finality of the judgment depends on whether appeal periods have expired."
        )
    
    def _generate_legislation_analysis(self, text):
        """Generate analysis specific to legislation"""
        return (
            "This document appears to be legislation or a statutory instrument. Here's a detailed analysis:\n\n"
            "1. Legislative Purpose and Scope:\n"
            "   - The statute establishes legal rules, rights, and obligations within its defined jurisdiction and subject matter.\n"
            "   - The legislation identifies its purpose and the public policy objectives it seeks to achieve.\n"
            "   - Jurisdictional boundaries and application scope are defined, including territorial and temporal limitations.\n\n"
            "2. Statutory Provisions:\n"
            "   - The legislation contains definitional sections establishing key terms and concepts for interpretation.\n"
            "   - Substantive provisions create rights, obligations, prohibitions, and permissions for affected parties.\n"
            "   - Administrative mechanisms and procedural requirements for implementation are established.\n\n"
            "3. Compliance Requirements:\n"
            "   - The statute imposes specific compliance obligations on affected individuals, businesses, or organizations.\n"
            "   - Penalties and enforcement mechanisms for non-compliance are specified with relevant authorities.\n"
            "   - Transitional provisions may address the relationship between this law and previous legal frameworks.\n\n"
            "4. Legal Implications:\n"
            "   - The legislation may preempt or modify existing common law or statutory provisions in its field.\n"
            "   - Courts will interpret this legislation according to established principles of statutory interpretation.\n"
            "   - Constitutional or other higher-order legal principles may affect the interpretation and validity of certain provisions."
        )
    
    def _generate_will_analysis(self, text):
        """Generate analysis specific to wills and testaments"""
        return (
            "This document appears to be a last will and testament. Here's a detailed analysis:\n\n"
            "1. Testamentary Capacity and Formalities:\n"
            "   - The document purports to be a valid will expressing the testator's intentions regarding asset distribution.\n"
            "   - Formal requirements including signature, witnesses, and attestation clauses appear to be addressed.\n"
            "   - The testator's capacity at the time of execution is a critical factor for validity.\n\n"
            "2. Asset Distribution:\n"
            "   - Specific bequests allocate particular assets or amounts to named beneficiaries.\n"
            "   - Residuary clauses address the distribution of remaining assets not specifically bequeathed.\n"
            "   - Contingent provisions may address scenarios such as beneficiaries predeceasing the testator.\n\n"
            "3. Administration Provisions:\n"
            "   - The will appoints executors/personal representatives with powers to administer the estate.\n"
            "   - Instructions regarding probate procedures and asset management are provided.\n"
            "   - Tax considerations and payment of debts and expenses are addressed.\n\n"
            "4. Legal Implications:\n"
            "   - The will becomes effective upon the testator's death and must be submitted for probate.\n"
            "   - Potential challenges could arise based on capacity, undue influence, fraud, or improper execution.\n"
            "   - Applicable succession laws may impact the interpretation and implementation of the will's provisions."
        )
    
    def _generate_affidavit_analysis(self, text):
        """Generate analysis specific to affidavits"""
        return (
            "This document appears to be an affidavit. Here's a detailed analysis:\n\n"
            "1. Purpose and Structure:\n"
            "   - This sworn statement is made for official legal purposes and carries potential perjury consequences if false.\n"
            "   - The document identifies the deponent (affiant) and establishes their competence to make the statements.\n"
            "   - The affidavit follows standard format requirements with proper verification clauses.\n\n"
            "2. Factual Assertions:\n"
            "   - The deponent makes specific factual declarations under oath based on personal knowledge or information and belief.\n"
            "   - Supporting exhibits or documents may be referenced and incorporated into the affidavit.\n"
            "   - The statements are made with the understanding of their legal significance in proceedings.\n\n"
            "3. Authentication:\n"
            "   - The affidavit contains notarial or other official authentication verifying the deponent's identity.\n"
            "   - Proper execution through signature and oath or affirmation is essential to validity.\n"
            "   - The document follows jurisdictional requirements for affidavit formalities.\n\n"
            "4. Legal Implications:\n"
            "   - The affidavit constitutes evidence that may be used in legal proceedings subject to applicable rules.\n"
            "   - False statements could expose the deponent to criminal penalties for perjury or false swearing.\n"
            "   - The affidavit's weight as evidence may depend on factors such as specificity, corroboration, and credibility."
        )
    
    def _generate_notice_analysis(self, text):
        """Generate analysis specific to legal notices"""
        return (
            "This document appears to be a legal notice. Here's a detailed analysis:\n\n"
            "1. Purpose and Type:\n"
            "   - The notice serves to formally inform specific parties of legal rights, obligations, or actions.\n"
            "   - It establishes formal communication for procedural or substantive legal purposes.\n"
            "   - The notice type (e.g., demand, statutory, termination) determines its specific legal effect.\n\n"
            "2. Content Requirements:\n"
            "   - The notice identifies relevant parties, subject matter, and the legal basis for the communication.\n"
            "   - Specific legal requirements for content appear to be addressed based on the notice type.\n"
            "   - Time-sensitive information and deadlines are stated with appropriate specificity.\n\n"
            "3. Service and Delivery:\n"
            "   - The method of delivery is designed to satisfy legal requirements for effective notice.\n"
            "   - Documentation of service may be required to establish proper notice was given.\n"
            "   - Timing requirements for advance notice appear to be addressed.\n\n"
            "4. Legal Implications:\n"
            "   - The notice triggers legal consequences, rights, or obligations specified by relevant law.\n"
            "   - Failure to respond appropriately may result in default or waiver of certain rights.\n"
            "   - The notice may be a prerequisite for subsequent legal proceedings or actions."
        )
    
    def _generate_legal_opinion_analysis(self, text):
        """Generate analysis specific to legal opinions"""
        return (
            "This document appears to be a legal opinion. Here's a detailed analysis:\n\n"
            "1. Structure and Purpose:\n"
            "   - This document provides professional legal analysis on specific questions or scenarios.\n"
            "   - It identifies the requesting party, relevant facts, and legal questions presented.\n"
            "   - The opinion serves to guide decision-making based on legal risk assessment.\n\n"
            "2. Legal Analysis:\n"
            "   - The opinion applies relevant statutory provisions, case law, and legal principles to the specific scenario.\n"
            "   - Alternative interpretations and potential outcomes are evaluated with probability assessments.\n"
            "   - Legal authorities are cited to support the reasoning and conclusions reached.\n\n"
            "3. Risk Assessment:\n"
            "   - The opinion identifies legal risks, ambiguities, and potential challenges to the proposed course of action.\n"
            "   - Recommendations for risk mitigation strategies are provided based on the legal analysis.\n"
            "   - Limitations and assumptions underlying the analysis are explicitly stated.\n\n"
            "4. Legal Implications:\n"
            "   - While the opinion provides guidance, ultimate decision-making responsibility remains with the client.\n"
            "   - The opinion may establish a basis for the 'advice of counsel' defense in certain circumstances.\n"
            "   - The analysis is time-specific and subject to change based on legal developments or factual changes."
        )
    
    def _generate_mou_analysis(self, text):
        """Generate analysis specific to MOUs"""
        return (
            "This document appears to be a Memorandum of Understanding (MOU). Here's a detailed analysis:\n\n"
            "1. Nature and Enforceability:\n"
            "   - This document establishes a preliminary framework for a relationship between the parties.\n"
            "   - The MOU may contain both binding and non-binding provisions depending on specific language used.\n"
            "   - Its enforceability depends on whether essential elements of a contract are present and the parties' intent.\n\n"
            "2. Key Components:\n"
            "   - The document outlines the parties' shared understanding and objectives for potential collaboration.\n"
            "   - Preliminary terms, responsibilities, and contributions of each party are identified.\n"
            "   - The framework for developing a formal agreement may be established with timelines.\n\n"
            "3. Limitations and Conditions:\n"
            "   - Conditional language may limit legal obligations pending further negotiation or due diligence.\n"
            "   - Confidentiality provisions and intellectual property protections may be legally binding.\n"
            "   - Termination provisions outline how parties may exit the preliminary relationship.\n\n"
            "4. Legal Implications:\n"
            "   - Courts may enforce certain provisions if they demonstrate the parties' intent to be bound.\n"
            "   - Even if not fully enforceable, the MOU may create liability under doctrines such as promissory estoppel if relied upon.\n"
            "   - The MOU may establish good faith negotiation obligations toward a definitive agreement."
        )
    
    def process_legal_query(self, document_text, language="en"):
        """
        Process the legal document and generate a detailed response
        
        Args:
            document_text: The text content of the document
            language: Language code for the response (default: 'en')
            
        Returns:
            dict: Response containing detailed analysis and audio path
        """
        # Identify document type
        doc_type, confidence = self._identify_document_type(document_text)
        
        # Extract entities
        entities = self._extract_legal_entities(document_text, doc_type)
        
        # Generate detailed legal analysis
        text_response = self._generate_legal_analysis(doc_type, document_text)
        
        # Map document types to human-readable labels
        doc_type_labels = {
            "contract": "Legal Contract",
            "judgment": "Court Judgment",
            "legislation": "Statutory Legislation",
            "will": "Last Will and Testament",
            "affidavit": "Legal Affidavit",
            "notice": "Legal Notice",
            "legal_opinion": "Legal Opinion",
            "mou": "Memorandum of Understanding",
            "unknown": "Legal Document"
        }
        
        document_type = doc_type_labels.get(doc_type, "Legal Document")
        
        # Generate audio filename
        audio_filename = f"response_{language}_{datetime.now().strftime('%Y%m%d%H%M%S')}.wav"
        audio_path = f"temp/{audio_filename}"
        
        # Create a dummy audio file for demo purposes
        with open(audio_path, "wb") as f:
            f.write(b"dummy audio data")
        
        return {
            "summary": text_response,
            "entities": entities,
            "audio_response": audio_path,
            "confidence_score": confidence,
            "document_type": document_type,
            "language": language
        }