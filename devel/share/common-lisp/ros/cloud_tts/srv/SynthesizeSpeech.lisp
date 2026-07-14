; Auto-generated. Do not edit!


(cl:in-package cloud_tts-srv)


;//! \htmlinclude SynthesizeSpeech-request.msg.html

(cl:defclass <SynthesizeSpeech-request> (roslisp-msg-protocol:ros-message)
  ((text
    :reader text
    :initarg :text
    :type cl:string
    :initform "")
   (play_audio
    :reader play_audio
    :initarg :play_audio
    :type cl:boolean
    :initform cl:nil))
)

(cl:defclass SynthesizeSpeech-request (<SynthesizeSpeech-request>)
  ())

(cl:defmethod cl:initialize-instance :after ((m <SynthesizeSpeech-request>) cl:&rest args)
  (cl:declare (cl:ignorable args))
  (cl:unless (cl:typep m 'SynthesizeSpeech-request)
    (roslisp-msg-protocol:msg-deprecation-warning "using old message class name cloud_tts-srv:<SynthesizeSpeech-request> is deprecated: use cloud_tts-srv:SynthesizeSpeech-request instead.")))

(cl:ensure-generic-function 'text-val :lambda-list '(m))
(cl:defmethod text-val ((m <SynthesizeSpeech-request>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader cloud_tts-srv:text-val is deprecated.  Use cloud_tts-srv:text instead.")
  (text m))

(cl:ensure-generic-function 'play_audio-val :lambda-list '(m))
(cl:defmethod play_audio-val ((m <SynthesizeSpeech-request>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader cloud_tts-srv:play_audio-val is deprecated.  Use cloud_tts-srv:play_audio instead.")
  (play_audio m))
(cl:defmethod roslisp-msg-protocol:serialize ((msg <SynthesizeSpeech-request>) ostream)
  "Serializes a message object of type '<SynthesizeSpeech-request>"
  (cl:let ((__ros_str_len (cl:length (cl:slot-value msg 'text))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) __ros_str_len) ostream))
  (cl:map cl:nil #'(cl:lambda (c) (cl:write-byte (cl:char-code c) ostream)) (cl:slot-value msg 'text))
  (cl:write-byte (cl:ldb (cl:byte 8 0) (cl:if (cl:slot-value msg 'play_audio) 1 0)) ostream)
)
(cl:defmethod roslisp-msg-protocol:deserialize ((msg <SynthesizeSpeech-request>) istream)
  "Deserializes a message object of type '<SynthesizeSpeech-request>"
    (cl:let ((__ros_str_len 0))
      (cl:setf (cl:ldb (cl:byte 8 0) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:slot-value msg 'text) (cl:make-string __ros_str_len))
      (cl:dotimes (__ros_str_idx __ros_str_len msg)
        (cl:setf (cl:char (cl:slot-value msg 'text) __ros_str_idx) (cl:code-char (cl:read-byte istream)))))
    (cl:setf (cl:slot-value msg 'play_audio) (cl:not (cl:zerop (cl:read-byte istream))))
  msg
)
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql '<SynthesizeSpeech-request>)))
  "Returns string type for a service object of type '<SynthesizeSpeech-request>"
  "cloud_tts/SynthesizeSpeechRequest")
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql 'SynthesizeSpeech-request)))
  "Returns string type for a service object of type 'SynthesizeSpeech-request"
  "cloud_tts/SynthesizeSpeechRequest")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql '<SynthesizeSpeech-request>)))
  "Returns md5sum for a message object of type '<SynthesizeSpeech-request>"
  "34da7af1fde48d1628d738c7d04b1734")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql 'SynthesizeSpeech-request)))
  "Returns md5sum for a message object of type 'SynthesizeSpeech-request"
  "34da7af1fde48d1628d738c7d04b1734")
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql '<SynthesizeSpeech-request>)))
  "Returns full string definition for message of type '<SynthesizeSpeech-request>"
  (cl:format cl:nil "string text~%bool play_audio~%~%~%"))
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql 'SynthesizeSpeech-request)))
  "Returns full string definition for message of type 'SynthesizeSpeech-request"
  (cl:format cl:nil "string text~%bool play_audio~%~%~%"))
(cl:defmethod roslisp-msg-protocol:serialization-length ((msg <SynthesizeSpeech-request>))
  (cl:+ 0
     4 (cl:length (cl:slot-value msg 'text))
     1
))
(cl:defmethod roslisp-msg-protocol:ros-message-to-list ((msg <SynthesizeSpeech-request>))
  "Converts a ROS message object to a list"
  (cl:list 'SynthesizeSpeech-request
    (cl:cons ':text (text msg))
    (cl:cons ':play_audio (play_audio msg))
))
;//! \htmlinclude SynthesizeSpeech-response.msg.html

(cl:defclass <SynthesizeSpeech-response> (roslisp-msg-protocol:ros-message)
  ((success
    :reader success
    :initarg :success
    :type cl:boolean
    :initform cl:nil)
   (audio_path
    :reader audio_path
    :initarg :audio_path
    :type cl:string
    :initform "")
   (error_message
    :reader error_message
    :initarg :error_message
    :type cl:string
    :initform "")
   (processing_time
    :reader processing_time
    :initarg :processing_time
    :type cl:float
    :initform 0.0))
)

(cl:defclass SynthesizeSpeech-response (<SynthesizeSpeech-response>)
  ())

(cl:defmethod cl:initialize-instance :after ((m <SynthesizeSpeech-response>) cl:&rest args)
  (cl:declare (cl:ignorable args))
  (cl:unless (cl:typep m 'SynthesizeSpeech-response)
    (roslisp-msg-protocol:msg-deprecation-warning "using old message class name cloud_tts-srv:<SynthesizeSpeech-response> is deprecated: use cloud_tts-srv:SynthesizeSpeech-response instead.")))

(cl:ensure-generic-function 'success-val :lambda-list '(m))
(cl:defmethod success-val ((m <SynthesizeSpeech-response>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader cloud_tts-srv:success-val is deprecated.  Use cloud_tts-srv:success instead.")
  (success m))

(cl:ensure-generic-function 'audio_path-val :lambda-list '(m))
(cl:defmethod audio_path-val ((m <SynthesizeSpeech-response>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader cloud_tts-srv:audio_path-val is deprecated.  Use cloud_tts-srv:audio_path instead.")
  (audio_path m))

(cl:ensure-generic-function 'error_message-val :lambda-list '(m))
(cl:defmethod error_message-val ((m <SynthesizeSpeech-response>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader cloud_tts-srv:error_message-val is deprecated.  Use cloud_tts-srv:error_message instead.")
  (error_message m))

(cl:ensure-generic-function 'processing_time-val :lambda-list '(m))
(cl:defmethod processing_time-val ((m <SynthesizeSpeech-response>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader cloud_tts-srv:processing_time-val is deprecated.  Use cloud_tts-srv:processing_time instead.")
  (processing_time m))
(cl:defmethod roslisp-msg-protocol:serialize ((msg <SynthesizeSpeech-response>) ostream)
  "Serializes a message object of type '<SynthesizeSpeech-response>"
  (cl:write-byte (cl:ldb (cl:byte 8 0) (cl:if (cl:slot-value msg 'success) 1 0)) ostream)
  (cl:let ((__ros_str_len (cl:length (cl:slot-value msg 'audio_path))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) __ros_str_len) ostream))
  (cl:map cl:nil #'(cl:lambda (c) (cl:write-byte (cl:char-code c) ostream)) (cl:slot-value msg 'audio_path))
  (cl:let ((__ros_str_len (cl:length (cl:slot-value msg 'error_message))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) __ros_str_len) ostream))
  (cl:map cl:nil #'(cl:lambda (c) (cl:write-byte (cl:char-code c) ostream)) (cl:slot-value msg 'error_message))
  (cl:let ((bits (roslisp-utils:encode-single-float-bits (cl:slot-value msg 'processing_time))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) bits) ostream))
)
(cl:defmethod roslisp-msg-protocol:deserialize ((msg <SynthesizeSpeech-response>) istream)
  "Deserializes a message object of type '<SynthesizeSpeech-response>"
    (cl:setf (cl:slot-value msg 'success) (cl:not (cl:zerop (cl:read-byte istream))))
    (cl:let ((__ros_str_len 0))
      (cl:setf (cl:ldb (cl:byte 8 0) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:slot-value msg 'audio_path) (cl:make-string __ros_str_len))
      (cl:dotimes (__ros_str_idx __ros_str_len msg)
        (cl:setf (cl:char (cl:slot-value msg 'audio_path) __ros_str_idx) (cl:code-char (cl:read-byte istream)))))
    (cl:let ((__ros_str_len 0))
      (cl:setf (cl:ldb (cl:byte 8 0) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:slot-value msg 'error_message) (cl:make-string __ros_str_len))
      (cl:dotimes (__ros_str_idx __ros_str_len msg)
        (cl:setf (cl:char (cl:slot-value msg 'error_message) __ros_str_idx) (cl:code-char (cl:read-byte istream)))))
    (cl:let ((bits 0))
      (cl:setf (cl:ldb (cl:byte 8 0) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) bits) (cl:read-byte istream))
    (cl:setf (cl:slot-value msg 'processing_time) (roslisp-utils:decode-single-float-bits bits)))
  msg
)
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql '<SynthesizeSpeech-response>)))
  "Returns string type for a service object of type '<SynthesizeSpeech-response>"
  "cloud_tts/SynthesizeSpeechResponse")
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql 'SynthesizeSpeech-response)))
  "Returns string type for a service object of type 'SynthesizeSpeech-response"
  "cloud_tts/SynthesizeSpeechResponse")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql '<SynthesizeSpeech-response>)))
  "Returns md5sum for a message object of type '<SynthesizeSpeech-response>"
  "34da7af1fde48d1628d738c7d04b1734")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql 'SynthesizeSpeech-response)))
  "Returns md5sum for a message object of type 'SynthesizeSpeech-response"
  "34da7af1fde48d1628d738c7d04b1734")
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql '<SynthesizeSpeech-response>)))
  "Returns full string definition for message of type '<SynthesizeSpeech-response>"
  (cl:format cl:nil "bool success~%string audio_path~%string error_message~%float32 processing_time~%~%~%~%"))
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql 'SynthesizeSpeech-response)))
  "Returns full string definition for message of type 'SynthesizeSpeech-response"
  (cl:format cl:nil "bool success~%string audio_path~%string error_message~%float32 processing_time~%~%~%~%"))
(cl:defmethod roslisp-msg-protocol:serialization-length ((msg <SynthesizeSpeech-response>))
  (cl:+ 0
     1
     4 (cl:length (cl:slot-value msg 'audio_path))
     4 (cl:length (cl:slot-value msg 'error_message))
     4
))
(cl:defmethod roslisp-msg-protocol:ros-message-to-list ((msg <SynthesizeSpeech-response>))
  "Converts a ROS message object to a list"
  (cl:list 'SynthesizeSpeech-response
    (cl:cons ':success (success msg))
    (cl:cons ':audio_path (audio_path msg))
    (cl:cons ':error_message (error_message msg))
    (cl:cons ':processing_time (processing_time msg))
))
(cl:defmethod roslisp-msg-protocol:service-request-type ((msg (cl:eql 'SynthesizeSpeech)))
  'SynthesizeSpeech-request)
(cl:defmethod roslisp-msg-protocol:service-response-type ((msg (cl:eql 'SynthesizeSpeech)))
  'SynthesizeSpeech-response)
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql 'SynthesizeSpeech)))
  "Returns string type for a service object of type '<SynthesizeSpeech>"
  "cloud_tts/SynthesizeSpeech")