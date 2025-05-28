import re
import nltk
from nltk.corpus import stopwords
from fuzzywuzzy import fuzz
import string

nltk.download('stopwords', quiet=True)

SPECIAL_TOKENS = {"<MOVIE_TITLE>", "<DIRECTOR_NAME>", "<ACTOR_NAME>"}

def normalize_for_matching(text):
    """Normalize text for matching purposes only."""
    return re.sub(r"[^\w\s]", "", text.lower())

def find_title_mentions(text, title):
    """
    Find all exact, case-insensitive, whole-word matches of the movie title.
    Returns a list of (start, end, tag) tuples.
    """
    matches = []
    if not title or len(title) < 2:
        return matches
    
    # Create pattern that handles word boundaries properly
    pattern = r'\b' + re.escape(title) + r'\b'
    
    for m in re.finditer(pattern, text, flags=re.IGNORECASE):
        matches.append((m.start(), m.end(), "<MOVIE_TITLE>"))
    
    return matches

def find_name_mentions(text, names, min_ratio=85):
    """
    Find matches for director/actor names in text with improved accuracy.
    """
    matches = []
    
    for name, tag in names:
        if not name or len(name.split()) < 2:
            continue
            
        # Try exact match first (case-insensitive)
        pattern = r'\b' + re.escape(name) + r'\b'
        for m in re.finditer(pattern, text, flags=re.IGNORECASE):
            matches.append((m.start(), m.end(), tag))
        
        # Try possessive form (e.g., "Nolan's" for "Christopher Nolan")
        last_name = name.split()[-1]
        if len(last_name) > 2:  # Avoid matching very short names
            possessive_pattern = r'\b' + re.escape(last_name) + r"'s?\b"
            for m in re.finditer(possessive_pattern, text, flags=re.IGNORECASE):
                # Verify this isn't part of a common word
                match_text = text[m.start():m.end()].lower()
                if not is_common_word_with_s(match_text.rstrip("'s")):
                    matches.append((m.start(), m.end(), tag))
        
        # Try partial name matching with stricter criteria
        name_parts = name.lower().split()
        if len(name_parts) >= 2:
            # Look for first + last name
            first_last_pattern = r'\b' + re.escape(name_parts[0]) + r'\s+' + re.escape(name_parts[-1]) + r'\b'
            for m in re.finditer(first_last_pattern, text, flags=re.IGNORECASE):
                matches.append((m.start(), m.end(), tag))
            
            # Look for just last name if it's distinctive enough
            if len(name_parts[-1]) >= 4 and name_parts[-1] not in get_common_words():
                last_name_pattern = r'\b' + re.escape(name_parts[-1]) + r'\b'
                for m in re.finditer(last_name_pattern, text, flags=re.IGNORECASE):
                    # Check context to avoid false positives
                    if is_likely_name_reference(text, m.start(), m.end()):
                        matches.append((m.start(), m.end(), tag))
    
    return matches

def is_common_word_with_s(word):
    """Check if a word is a common English word that might end with 's."""
    common_words = {
        'his', 'hers', 'its', 'theirs', 'ours', 'yours', 'this', 'that',
        'was', 'has', 'does', 'goes', 'comes', 'makes', 'takes', 'gives',
        'seems', 'looks', 'feels', 'sounds', 'appears', 'becomes'
    }
    return word.lower() in common_words

def get_common_words():
    """Get a set of common English words to avoid matching."""
    return {
        'the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have', 'it',
        'for', 'not', 'on', 'with', 'he', 'as', 'you', 'do', 'at', 'this',
        'but', 'his', 'by', 'from', 'they', 'we', 'say', 'her', 'she', 'or',
        'an', 'will', 'my', 'one', 'all', 'would', 'there', 'their', 'what',
        'so', 'up', 'out', 'if', 'about', 'who', 'get', 'which', 'go', 'me',
        'when', 'make', 'can', 'like', 'time', 'no', 'just', 'him', 'know',
        'take', 'people', 'into', 'year', 'your', 'good', 'some', 'could',
        'them', 'see', 'other', 'than', 'then', 'now', 'look', 'only', 'come',
        'its', 'over', 'think', 'also', 'back', 'after', 'use', 'two', 'how',
        'our', 'work', 'first', 'well', 'way', 'even', 'new', 'want', 'because',
        'any', 'these', 'give', 'day', 'most', 'us', 'still', 'find', 'tell',
        'really', 'dark', 'great', 'movie', 'film', 'scene', 'character', 'story',
        'plot', 'director', 'actor', 'actress', 'hero', 'villain', 'killer',
        'murder', 'death', 'child', 'mind', 'moral', 'figure', 'foundation'
    }

def is_likely_name_reference(text, start, end):
    """Check if a match is likely to be a name reference based on context."""
    # Look at surrounding context
    context_start = max(0, start - 20)
    context_end = min(len(text), end + 20)
    context = text[context_start:context_end].lower()
    
    # Positive indicators
    name_indicators = ['directed by', 'starring', 'actor', 'actress', 'star', 
                      'performance', 'played by', 'cast', 'role']
    
    # Negative indicators (words that suggest it's not a name)
    not_name_indicators = ['the', 'a', 'an', 'is', 'was', 'were', 'are',
                           'his', 'her', 'its', 'their', 'this', 'that']
    
    # Check for positive indicators
    for indicator in name_indicators:
        if indicator in context:
            return True
    
    # Check if the word immediately before is a negative indicator
    word_before = text[max(0, start-10):start].strip().split()[-1:] if start > 0 else []
    if word_before and word_before[0].lower() in not_name_indicators:
        return False
    
    return True

def remove_overlapping(matches):
    """Remove overlapping matches, keeping the longest ones."""
    if not matches:
        return []
    
    # Sort by start position, then by length (longest first)
    matches = sorted(matches, key=lambda x: (x[0], -(x[1]-x[0])))
    
    result = []
    last_end = -1
    
    for start, end, tag in matches:
        if start >= last_end:
            result.append((start, end, tag))
            last_end = end
    
    return result

def preprocess_movie_review(text, movies, title):
    """
    Preprocess a movie review with improved entity recognition.
    """
    if title not in movies:
        # Just do basic preprocessing if movie not in dictionary
        text_lower = text.lower()
        text_no_punct = re.sub(r"[^\w\s]", "", text_lower)
        words = text_no_punct.split()
        stops = set(stopwords.words("english"))
        cleaned = [w for w in words if w not in stops]
        return " ".join(cleaned)
    
    directors, actors = movies[title]
    
    # Find all entity matches
    entity_matches = []
    
    # Find title mentions
    entity_matches.extend(find_title_mentions(text, title))
    
    # Find director and actor mentions
    entity_matches.extend(find_name_mentions(text, [(d, "<DIRECTOR_NAME>") for d in directors]))
    entity_matches.extend(find_name_mentions(text, [(a, "<ACTOR_NAME>") for a in actors]))
    
    # Remove overlapping matches
    entity_matches = remove_overlapping(entity_matches)
    
    # Replace entities in text (from end to start to preserve indices)
    new_text = text
    for start, end, tag in sorted(entity_matches, key=lambda x: -x[0]):
        new_text = new_text[:start] + tag + new_text[end:]
    
    # Lowercase and remove punctuation
    new_text = new_text.lower()
    
    # Preserve special tokens while removing punctuation
    for token in SPECIAL_TOKENS:
        new_text = new_text.replace(token.lower(), f" {token} ")
    
    # Remove punctuation except for angle brackets
    new_text = re.sub(r"[^\w\s<>]", " ", new_text)
    
    # Tokenize
    words = new_text.split()
    
    # Remove stopwords except special tokens
    stops = set(stopwords.words("english"))
    cleaned = [w for w in words if w in SPECIAL_TOKENS or w not in stops]
    
    return " ".join(cleaned)

# Example usage
if __name__ == "__main__":
    # Example movie dictionary
    movies = {
        'Se7en': [
            ['David Fincher'],
            ['Brad Pitt', 'Morgan Freeman', 'Gwyneth Paltrow']
        ],
        'The Matrix': [
            ['Lana Wachowski', 'Lilly Wachowski'],
            ['Keanu Reeves', 'Laurence Fishburne', 'Carrie-Anne Moss']
        ]
    }
    
    # Test with your problematic examples
    review1 = """I don't understand why people think this is a good movie. The plot is predictable yet not really believable, the hero is unlikeable and the villain, who is supposed to be the movie's moral foundation (go figure *that* one), ultimately pulls the rug out from underneath the movie at the end.

The scene where Brad Pitt allows the killer to escape was irritatingly hard to believe. And what was the Gynneth Paltrow character's (not to mention her unborn child) sin? The killer was careful to choose people who (at least in his mind) deserved to die yet at the crucial climax he completely broke with his pattern in a most incredible way.

And where does a "moral" serial killer come from? Seems like an oxymoron, but of course in the end we see that he's not moral after all. Still, the whole concept rings hollow and leaves one wondering what the point of the movie was anyway? It seems like it was just a story created to give the film makers a chance to show grisly murder scenes one after another in an attempt to shock us."""
    
    review2 = """I don't understand why people think this is a good movie. The plot is predictable 
    yet not really believable, the hero is unlikeable and the villain, who is supposed to be the 
    movie's moral foundation (go figure *that* one), ultimately pulls the rug out from underneath 
    the movie at the end. The scene where Brad Pitt allows the killer to escape was irritatingly 
    hard to believe. And what was the Gynneth Paltrow character's (not to mention her unborn child) 
    sin? The killer was careful to choose people who (at least in his mind) deserved to die yet 
    at the crucial climax he completely broke with his pattern in a most incredible way."""
    
    print("Review 1:")
    print("Processed:", preprocess_movie_review(review1, movies, "Se7en"))
    print("\nReview 2:")
    print("Processed:", preprocess_movie_review(review2, movies, "Se7en"))