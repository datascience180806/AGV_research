class DiagnosisEvaluator:
    """Evaluates AI diagnosis quality against scenario ground truth"""
    
    @staticmethod
    def evaluate(diagnoses: list, ground_truth: dict) -> dict:
        """
        Args:
            diagnoses: A list of dicts: {"elapsed_time": float, "diagnosis": dict}
            ground_truth: Ground truth dict from the scenario config
            
        Returns:
            A dictionary containing evaluation scores:
            - detection_accuracy (float, 0.0 to 100.0)
            - false_positive_count (int)
            - detection_latency_seconds (float or None)
            - correct_root_cause (bool)
        """
        expected_anomalies = ground_truth.get("expected_anomalies", [])
        
        # Track if expected anomalies were detected
        detected_anomalies = []
        false_positive_count = 0
        first_detection_time = None
        correct_root_cause = False
        
        for record in diagnoses:
            elapsed_time = record.get("elapsed_time", 0.0)
            diagnosis = record.get("diagnosis", {})
            anomalies = diagnosis.get("anomalies_detected", [])
            
            for anomaly in anomalies:
                anom_type = anomaly.get("anomaly_type")
                if anom_type == "none" or not anom_type:
                    continue
                
                # Check if this matches any expected anomaly
                matched = False
                for expected in expected_anomalies:
                    if (expected["type"] == anom_type and 
                        expected["affected_agv"] == anomaly.get("affected_agv")):
                        matched = True
                        if first_detection_time is None and elapsed_time >= expected["onset_time_s"]:
                            first_detection_time = elapsed_time
                            # Simple keyword check for root cause
                            root_cause_text = anomaly.get("root_cause_analysis", "").lower()
                            if "leak" in root_cause_text or "cell" in root_cause_text or "battery" in root_cause_text:
                                correct_root_cause = True
                        break
                
                if matched:
                    if (anom_type, anomaly.get("affected_agv")) not in detected_anomalies:
                        detected_anomalies.append((anom_type, anomaly.get("affected_agv")))
                else:
                    false_positive_count += 1
                    
        # Calculate detection accuracy
        total_expected = len(expected_anomalies)
        if total_expected > 0:
            accuracy = (len(detected_anomalies) / total_expected) * 100.0
        else:
            accuracy = 100.0 if false_positive_count == 0 else 0.0
            
        # Latency calculation
        latency = None
        if first_detection_time is not None and expected_anomalies:
            onset = expected_anomalies[0]["onset_time_s"]
            latency = max(0.0, first_detection_time - onset)
            
        return {
            "detection_accuracy": accuracy,
            "false_positive_count": false_positive_count,
            "detection_latency_seconds": latency,
            "correct_root_cause": correct_root_cause
        }
