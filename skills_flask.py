from flask import Flask, request, jsonify
import pandas as pd


app = Flask(__name__)
app.config['TRUST_PROXY'] = True


# Initialize your analyzer (consider loading your dataset here as well)
# Define OccupationSkillAnalyzer class that will be used to analyze the dataset
class OccupationSkillAnalyzer:
    def __init__(self):
        # Hardwire the dataset path here
        dataset_path = 'Data/occupation_skills.csv'
        self.data = pd.read_csv(dataset_path)
        # Normalize columns for case-insensitive searching
        self.data['occupationLabel_normalized'] = self.data['occupationLabel'].str.lower()
        self.data['alt_occupationLabel_normalized'] = self.data['alt_occupationLabel'].str.lower().str.split('\n').apply(lambda x: x if isinstance(x, list) else [])
    
    def analyze_input(self, input_string):
        normalized_input = input_string.strip().lower()
        return self._find_top_skills_for_occupation(normalized_input)
    
    def _find_top_skills_for_occupation(self, occupation_input):
        direct_matches = self.data[self.data['occupationLabel_normalized'] == occupation_input]
        
        if direct_matches.empty:
            matches = self.data[self.data['alt_occupationLabel_normalized'].apply(lambda x: occupation_input in x if isinstance(x, list) else False)]
        else:
            matches = direct_matches
            
        if matches.empty:
            # If no direct matches, try partial matches
            return self._find_top_skills_for_occupation_partial_matches(occupation_input)
        
        skills_frequency = matches['skillLabel'].value_counts().head(10)
        return skills_frequency if not skills_frequency.empty else self._find_top_skills_for_occupation_partial_matches(occupation_input)
    
    def _find_top_skills_for_occupation_partial_matches(self, occupation_input, min_length=4):
        def matches_occupation(row):
            if occupation_input in row['occupationLabel_normalized']:
                return True
            return any(occupation_input in alt for alt in row['alt_occupationLabel_normalized'])

        filtered_data = self.data[self.data.apply(matches_occupation, axis=1)]
        
        while filtered_data.empty and len(occupation_input) > min_length:
            shortened_input = occupation_input[:-1]
            if shortened_input:
                return self._find_top_skills_for_occupation_partial_matches(shortened_input, min_length)
        else:
            skills_frequency = filtered_data['skillLabel'].value_counts().head(10)
            return skills_frequency if not skills_frequency.empty else self._find_occupations_for_skill(occupation_input)
        
        return self._find_occupations_for_skill(occupation_input)

    def _find_occupations_for_skill(self, skill_input):
        temp_data = self.data.copy()
        skill_input_normalized = skill_input.lower().strip()
        temp_data['skillLabel_normalized'] = temp_data['skillLabel'].str.lower()
        temp_data['alt_skillLabel_normalized'] = temp_data['alt_skillLabel'].apply(lambda x: x.lower().split('\n') if isinstance(x, str) else [])
        direct_matches = temp_data[temp_data['skillLabel_normalized'] == skill_input_normalized]
        if direct_matches.empty:
            matches = temp_data[temp_data['alt_skillLabel_normalized'].apply(lambda x: skill_input_normalized in x)]
        else:
            matches = direct_matches
        if matches.empty:
            matches = temp_data[
                temp_data['skillLabel_normalized'].str.contains(skill_input_normalized) |
                temp_data['alt_skillLabel_normalized'].apply(lambda x: any(skill_input_normalized in alt for alt in x))
            ]
        if matches.empty:
            return "No match found."
        
        occupations_frequency = matches['occupationLabel'].value_counts().head(10)
        return occupations_frequency if not occupations_frequency.empty else "No match found."


# Initialize the analyzer
analyzer = OccupationSkillAnalyzer()

@app.route('/')
def home():
    return 'Skills Database!'

@app.route('/analyze', methods=['POST'])
def analyze_occupation():
    data = request.json
    input_string = data.get('inputString', '')
    
    if not input_string:
        return jsonify({'error': 'Input string is required.'}), 400
    
    result = analyzer.analyze_input(input_string)
    return jsonify({'skills': result.to_dict()}), 200

if __name__ == '__main__':
    app.run(debug=True , host='0.0.0.0', port=8000)
