@app.route('/api/analyze_emotion', methods=['POST'])
def analyze_emotion():
    """Analyze emotion from voice command"""
    try:
        data = request.get_json()
        user_id = data.get('user_id', 'default')
        command_text = data.get('text', '')
        confidence = data.get('confidence', 0.8)
        
        if not command_text:
            return jsonify({'error': 'No text provided'}), 400
        
        # Detect emotion from text and voice patterns
        emotion = emotional_ai.detect_emotion_from_voice_patterns(command_text, confidence)
        
        # Get emotional response
        emotional_response = emotional_ai.get_emotional_response(emotion, user_id)
        
        # Adjust response style based on user patterns
        adjusted_response = emotional_ai.adjust_response_style(
            user_id, 
            emotional_response['response']
        )
        
        return jsonify({
            'detected_emotion': emotion,
            'empathy_level': emotional_response['empathy_level'],
            'emotional_response': adjusted_response,
            'suggestions': emotional_response['suggestions'],
            'emotion_patterns': emotional_ai.get_emotion_patterns(user_id)
        })
        
    except Exception as e:
        logger.error(f"Emotion analysis error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/emotion_history', methods=['GET'])
def get_emotion_history():
    """Get user's emotion history and patterns"""
    try:
        user_id = request.args.get('user_id', 'default')
        patterns = emotional_ai.get_emotion_patterns(user_id)
        
        return jsonify({
            'user_id': user_id,
            'emotion_patterns': patterns,
            'recommendations': emotional_ai.get_emotion_suggestions(
                patterns.get('recent_trend', 'neutral')
            )
        })
        
    except Exception as e:
        logger.error(f"Emotion history error: {e}")
        return jsonify({'error': str(e)}), 500