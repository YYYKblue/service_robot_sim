;; Auto-generated. Do not edit!


(when (boundp 'voice_keyword_extractor::ExtractKeyword)
  (if (not (find-package "VOICE_KEYWORD_EXTRACTOR"))
    (make-package "VOICE_KEYWORD_EXTRACTOR"))
  (shadow 'ExtractKeyword (find-package "VOICE_KEYWORD_EXTRACTOR")))
(unless (find-package "VOICE_KEYWORD_EXTRACTOR::EXTRACTKEYWORD")
  (make-package "VOICE_KEYWORD_EXTRACTOR::EXTRACTKEYWORD"))
(unless (find-package "VOICE_KEYWORD_EXTRACTOR::EXTRACTKEYWORDREQUEST")
  (make-package "VOICE_KEYWORD_EXTRACTOR::EXTRACTKEYWORDREQUEST"))
(unless (find-package "VOICE_KEYWORD_EXTRACTOR::EXTRACTKEYWORDRESPONSE")
  (make-package "VOICE_KEYWORD_EXTRACTOR::EXTRACTKEYWORDRESPONSE"))

(in-package "ROS")





(defclass voice_keyword_extractor::ExtractKeywordRequest
  :super ros::object
  :slots (_start_recording _record_seconds ))

(defmethod voice_keyword_extractor::ExtractKeywordRequest
  (:init
   (&key
    ((:start_recording __start_recording) nil)
    ((:record_seconds __record_seconds) 0.0)
    )
   (send-super :init)
   (setq _start_recording __start_recording)
   (setq _record_seconds (float __record_seconds))
   self)
  (:start_recording
   (&optional (__start_recording :null))
   (if (not (eq __start_recording :null)) (setq _start_recording __start_recording)) _start_recording)
  (:record_seconds
   (&optional __record_seconds)
   (if __record_seconds (setq _record_seconds __record_seconds)) _record_seconds)
  (:serialization-length
   ()
   (+
    ;; bool _start_recording
    1
    ;; float32 _record_seconds
    4
    ))
  (:serialize
   (&optional strm)
   (let ((s (if strm strm
              (make-string-output-stream (send self :serialization-length)))))
     ;; bool _start_recording
       (if _start_recording (write-byte -1 s) (write-byte 0 s))
     ;; float32 _record_seconds
       (sys::poke _record_seconds (send s :buffer) (send s :count) :float) (incf (stream-count s) 4)
     ;;
     (if (null strm) (get-output-stream-string s))))
  (:deserialize
   (buf &optional (ptr- 0))
   ;; bool _start_recording
     (setq _start_recording (not (= 0 (sys::peek buf ptr- :char)))) (incf ptr- 1)
   ;; float32 _record_seconds
     (setq _record_seconds (sys::peek buf ptr- :float)) (incf ptr- 4)
   ;;
   self)
  )

(defclass voice_keyword_extractor::ExtractKeywordResponse
  :super ros::object
  :slots (_success _keyword _transcript _raw_result _error_message _processing_time ))

(defmethod voice_keyword_extractor::ExtractKeywordResponse
  (:init
   (&key
    ((:success __success) nil)
    ((:keyword __keyword) "")
    ((:transcript __transcript) "")
    ((:raw_result __raw_result) "")
    ((:error_message __error_message) "")
    ((:processing_time __processing_time) 0.0)
    )
   (send-super :init)
   (setq _success __success)
   (setq _keyword (string __keyword))
   (setq _transcript (string __transcript))
   (setq _raw_result (string __raw_result))
   (setq _error_message (string __error_message))
   (setq _processing_time (float __processing_time))
   self)
  (:success
   (&optional (__success :null))
   (if (not (eq __success :null)) (setq _success __success)) _success)
  (:keyword
   (&optional __keyword)
   (if __keyword (setq _keyword __keyword)) _keyword)
  (:transcript
   (&optional __transcript)
   (if __transcript (setq _transcript __transcript)) _transcript)
  (:raw_result
   (&optional __raw_result)
   (if __raw_result (setq _raw_result __raw_result)) _raw_result)
  (:error_message
   (&optional __error_message)
   (if __error_message (setq _error_message __error_message)) _error_message)
  (:processing_time
   (&optional __processing_time)
   (if __processing_time (setq _processing_time __processing_time)) _processing_time)
  (:serialization-length
   ()
   (+
    ;; bool _success
    1
    ;; string _keyword
    4 (length _keyword)
    ;; string _transcript
    4 (length _transcript)
    ;; string _raw_result
    4 (length _raw_result)
    ;; string _error_message
    4 (length _error_message)
    ;; float32 _processing_time
    4
    ))
  (:serialize
   (&optional strm)
   (let ((s (if strm strm
              (make-string-output-stream (send self :serialization-length)))))
     ;; bool _success
       (if _success (write-byte -1 s) (write-byte 0 s))
     ;; string _keyword
       (write-long (length _keyword) s) (princ _keyword s)
     ;; string _transcript
       (write-long (length _transcript) s) (princ _transcript s)
     ;; string _raw_result
       (write-long (length _raw_result) s) (princ _raw_result s)
     ;; string _error_message
       (write-long (length _error_message) s) (princ _error_message s)
     ;; float32 _processing_time
       (sys::poke _processing_time (send s :buffer) (send s :count) :float) (incf (stream-count s) 4)
     ;;
     (if (null strm) (get-output-stream-string s))))
  (:deserialize
   (buf &optional (ptr- 0))
   ;; bool _success
     (setq _success (not (= 0 (sys::peek buf ptr- :char)))) (incf ptr- 1)
   ;; string _keyword
     (let (n) (setq n (sys::peek buf ptr- :integer)) (incf ptr- 4) (setq _keyword (subseq buf ptr- (+ ptr- n))) (incf ptr- n))
   ;; string _transcript
     (let (n) (setq n (sys::peek buf ptr- :integer)) (incf ptr- 4) (setq _transcript (subseq buf ptr- (+ ptr- n))) (incf ptr- n))
   ;; string _raw_result
     (let (n) (setq n (sys::peek buf ptr- :integer)) (incf ptr- 4) (setq _raw_result (subseq buf ptr- (+ ptr- n))) (incf ptr- n))
   ;; string _error_message
     (let (n) (setq n (sys::peek buf ptr- :integer)) (incf ptr- 4) (setq _error_message (subseq buf ptr- (+ ptr- n))) (incf ptr- n))
   ;; float32 _processing_time
     (setq _processing_time (sys::peek buf ptr- :float)) (incf ptr- 4)
   ;;
   self)
  )

(defclass voice_keyword_extractor::ExtractKeyword
  :super ros::object
  :slots ())

(setf (get voice_keyword_extractor::ExtractKeyword :md5sum-) "e6ee6cf4f2ad6072c8d07a6cc7a7b46a")
(setf (get voice_keyword_extractor::ExtractKeyword :datatype-) "voice_keyword_extractor/ExtractKeyword")
(setf (get voice_keyword_extractor::ExtractKeyword :request) voice_keyword_extractor::ExtractKeywordRequest)
(setf (get voice_keyword_extractor::ExtractKeyword :response) voice_keyword_extractor::ExtractKeywordResponse)

(defmethod voice_keyword_extractor::ExtractKeywordRequest
  (:response () (instance voice_keyword_extractor::ExtractKeywordResponse :init)))

(setf (get voice_keyword_extractor::ExtractKeywordRequest :md5sum-) "e6ee6cf4f2ad6072c8d07a6cc7a7b46a")
(setf (get voice_keyword_extractor::ExtractKeywordRequest :datatype-) "voice_keyword_extractor/ExtractKeywordRequest")
(setf (get voice_keyword_extractor::ExtractKeywordRequest :definition-)
      "bool start_recording
float32 record_seconds
---
bool success
string keyword
string transcript
string raw_result
string error_message
float32 processing_time

")

(setf (get voice_keyword_extractor::ExtractKeywordResponse :md5sum-) "e6ee6cf4f2ad6072c8d07a6cc7a7b46a")
(setf (get voice_keyword_extractor::ExtractKeywordResponse :datatype-) "voice_keyword_extractor/ExtractKeywordResponse")
(setf (get voice_keyword_extractor::ExtractKeywordResponse :definition-)
      "bool start_recording
float32 record_seconds
---
bool success
string keyword
string transcript
string raw_result
string error_message
float32 processing_time

")



(provide :voice_keyword_extractor/ExtractKeyword "e6ee6cf4f2ad6072c8d07a6cc7a7b46a")


