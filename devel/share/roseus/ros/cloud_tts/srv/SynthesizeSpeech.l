;; Auto-generated. Do not edit!


(when (boundp 'cloud_tts::SynthesizeSpeech)
  (if (not (find-package "CLOUD_TTS"))
    (make-package "CLOUD_TTS"))
  (shadow 'SynthesizeSpeech (find-package "CLOUD_TTS")))
(unless (find-package "CLOUD_TTS::SYNTHESIZESPEECH")
  (make-package "CLOUD_TTS::SYNTHESIZESPEECH"))
(unless (find-package "CLOUD_TTS::SYNTHESIZESPEECHREQUEST")
  (make-package "CLOUD_TTS::SYNTHESIZESPEECHREQUEST"))
(unless (find-package "CLOUD_TTS::SYNTHESIZESPEECHRESPONSE")
  (make-package "CLOUD_TTS::SYNTHESIZESPEECHRESPONSE"))

(in-package "ROS")





(defclass cloud_tts::SynthesizeSpeechRequest
  :super ros::object
  :slots (_text _play_audio ))

(defmethod cloud_tts::SynthesizeSpeechRequest
  (:init
   (&key
    ((:text __text) "")
    ((:play_audio __play_audio) nil)
    )
   (send-super :init)
   (setq _text (string __text))
   (setq _play_audio __play_audio)
   self)
  (:text
   (&optional __text)
   (if __text (setq _text __text)) _text)
  (:play_audio
   (&optional (__play_audio :null))
   (if (not (eq __play_audio :null)) (setq _play_audio __play_audio)) _play_audio)
  (:serialization-length
   ()
   (+
    ;; string _text
    4 (length _text)
    ;; bool _play_audio
    1
    ))
  (:serialize
   (&optional strm)
   (let ((s (if strm strm
              (make-string-output-stream (send self :serialization-length)))))
     ;; string _text
       (write-long (length _text) s) (princ _text s)
     ;; bool _play_audio
       (if _play_audio (write-byte -1 s) (write-byte 0 s))
     ;;
     (if (null strm) (get-output-stream-string s))))
  (:deserialize
   (buf &optional (ptr- 0))
   ;; string _text
     (let (n) (setq n (sys::peek buf ptr- :integer)) (incf ptr- 4) (setq _text (subseq buf ptr- (+ ptr- n))) (incf ptr- n))
   ;; bool _play_audio
     (setq _play_audio (not (= 0 (sys::peek buf ptr- :char)))) (incf ptr- 1)
   ;;
   self)
  )

(defclass cloud_tts::SynthesizeSpeechResponse
  :super ros::object
  :slots (_success _audio_path _error_message _processing_time ))

(defmethod cloud_tts::SynthesizeSpeechResponse
  (:init
   (&key
    ((:success __success) nil)
    ((:audio_path __audio_path) "")
    ((:error_message __error_message) "")
    ((:processing_time __processing_time) 0.0)
    )
   (send-super :init)
   (setq _success __success)
   (setq _audio_path (string __audio_path))
   (setq _error_message (string __error_message))
   (setq _processing_time (float __processing_time))
   self)
  (:success
   (&optional (__success :null))
   (if (not (eq __success :null)) (setq _success __success)) _success)
  (:audio_path
   (&optional __audio_path)
   (if __audio_path (setq _audio_path __audio_path)) _audio_path)
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
    ;; string _audio_path
    4 (length _audio_path)
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
     ;; string _audio_path
       (write-long (length _audio_path) s) (princ _audio_path s)
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
   ;; string _audio_path
     (let (n) (setq n (sys::peek buf ptr- :integer)) (incf ptr- 4) (setq _audio_path (subseq buf ptr- (+ ptr- n))) (incf ptr- n))
   ;; string _error_message
     (let (n) (setq n (sys::peek buf ptr- :integer)) (incf ptr- 4) (setq _error_message (subseq buf ptr- (+ ptr- n))) (incf ptr- n))
   ;; float32 _processing_time
     (setq _processing_time (sys::peek buf ptr- :float)) (incf ptr- 4)
   ;;
   self)
  )

(defclass cloud_tts::SynthesizeSpeech
  :super ros::object
  :slots ())

(setf (get cloud_tts::SynthesizeSpeech :md5sum-) "34da7af1fde48d1628d738c7d04b1734")
(setf (get cloud_tts::SynthesizeSpeech :datatype-) "cloud_tts/SynthesizeSpeech")
(setf (get cloud_tts::SynthesizeSpeech :request) cloud_tts::SynthesizeSpeechRequest)
(setf (get cloud_tts::SynthesizeSpeech :response) cloud_tts::SynthesizeSpeechResponse)

(defmethod cloud_tts::SynthesizeSpeechRequest
  (:response () (instance cloud_tts::SynthesizeSpeechResponse :init)))

(setf (get cloud_tts::SynthesizeSpeechRequest :md5sum-) "34da7af1fde48d1628d738c7d04b1734")
(setf (get cloud_tts::SynthesizeSpeechRequest :datatype-) "cloud_tts/SynthesizeSpeechRequest")
(setf (get cloud_tts::SynthesizeSpeechRequest :definition-)
      "string text
bool play_audio
---
bool success
string audio_path
string error_message
float32 processing_time

")

(setf (get cloud_tts::SynthesizeSpeechResponse :md5sum-) "34da7af1fde48d1628d738c7d04b1734")
(setf (get cloud_tts::SynthesizeSpeechResponse :datatype-) "cloud_tts/SynthesizeSpeechResponse")
(setf (get cloud_tts::SynthesizeSpeechResponse :definition-)
      "string text
bool play_audio
---
bool success
string audio_path
string error_message
float32 processing_time

")



(provide :cloud_tts/SynthesizeSpeech "34da7af1fde48d1628d738c7d04b1734")


