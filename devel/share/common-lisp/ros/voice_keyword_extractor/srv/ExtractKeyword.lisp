; Auto-generated. Do not edit!


(cl:in-package voice_keyword_extractor-srv)


;//! \htmlinclude ExtractKeyword-request.msg.html

(cl:defclass <ExtractKeyword-request> (roslisp-msg-protocol:ros-message)
  ((start_recording
    :reader start_recording
    :initarg :start_recording
    :type cl:boolean
    :initform cl:nil)
   (record_seconds
    :reader record_seconds
    :initarg :record_seconds
    :type cl:float
    :initform 0.0))
)

(cl:defclass ExtractKeyword-request (<ExtractKeyword-request>)
  ())

(cl:defmethod cl:initialize-instance :after ((m <ExtractKeyword-request>) cl:&rest args)
  (cl:declare (cl:ignorable args))
  (cl:unless (cl:typep m 'ExtractKeyword-request)
    (roslisp-msg-protocol:msg-deprecation-warning "using old message class name voice_keyword_extractor-srv:<ExtractKeyword-request> is deprecated: use voice_keyword_extractor-srv:ExtractKeyword-request instead.")))

(cl:ensure-generic-function 'start_recording-val :lambda-list '(m))
(cl:defmethod start_recording-val ((m <ExtractKeyword-request>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader voice_keyword_extractor-srv:start_recording-val is deprecated.  Use voice_keyword_extractor-srv:start_recording instead.")
  (start_recording m))

(cl:ensure-generic-function 'record_seconds-val :lambda-list '(m))
(cl:defmethod record_seconds-val ((m <ExtractKeyword-request>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader voice_keyword_extractor-srv:record_seconds-val is deprecated.  Use voice_keyword_extractor-srv:record_seconds instead.")
  (record_seconds m))
(cl:defmethod roslisp-msg-protocol:serialize ((msg <ExtractKeyword-request>) ostream)
  "Serializes a message object of type '<ExtractKeyword-request>"
  (cl:write-byte (cl:ldb (cl:byte 8 0) (cl:if (cl:slot-value msg 'start_recording) 1 0)) ostream)
  (cl:let ((bits (roslisp-utils:encode-single-float-bits (cl:slot-value msg 'record_seconds))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) bits) ostream))
)
(cl:defmethod roslisp-msg-protocol:deserialize ((msg <ExtractKeyword-request>) istream)
  "Deserializes a message object of type '<ExtractKeyword-request>"
    (cl:setf (cl:slot-value msg 'start_recording) (cl:not (cl:zerop (cl:read-byte istream))))
    (cl:let ((bits 0))
      (cl:setf (cl:ldb (cl:byte 8 0) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) bits) (cl:read-byte istream))
    (cl:setf (cl:slot-value msg 'record_seconds) (roslisp-utils:decode-single-float-bits bits)))
  msg
)
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql '<ExtractKeyword-request>)))
  "Returns string type for a service object of type '<ExtractKeyword-request>"
  "voice_keyword_extractor/ExtractKeywordRequest")
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql 'ExtractKeyword-request)))
  "Returns string type for a service object of type 'ExtractKeyword-request"
  "voice_keyword_extractor/ExtractKeywordRequest")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql '<ExtractKeyword-request>)))
  "Returns md5sum for a message object of type '<ExtractKeyword-request>"
  "e6ee6cf4f2ad6072c8d07a6cc7a7b46a")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql 'ExtractKeyword-request)))
  "Returns md5sum for a message object of type 'ExtractKeyword-request"
  "e6ee6cf4f2ad6072c8d07a6cc7a7b46a")
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql '<ExtractKeyword-request>)))
  "Returns full string definition for message of type '<ExtractKeyword-request>"
  (cl:format cl:nil "bool start_recording~%float32 record_seconds~%~%~%"))
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql 'ExtractKeyword-request)))
  "Returns full string definition for message of type 'ExtractKeyword-request"
  (cl:format cl:nil "bool start_recording~%float32 record_seconds~%~%~%"))
(cl:defmethod roslisp-msg-protocol:serialization-length ((msg <ExtractKeyword-request>))
  (cl:+ 0
     1
     4
))
(cl:defmethod roslisp-msg-protocol:ros-message-to-list ((msg <ExtractKeyword-request>))
  "Converts a ROS message object to a list"
  (cl:list 'ExtractKeyword-request
    (cl:cons ':start_recording (start_recording msg))
    (cl:cons ':record_seconds (record_seconds msg))
))
;//! \htmlinclude ExtractKeyword-response.msg.html

(cl:defclass <ExtractKeyword-response> (roslisp-msg-protocol:ros-message)
  ((success
    :reader success
    :initarg :success
    :type cl:boolean
    :initform cl:nil)
   (keyword
    :reader keyword
    :initarg :keyword
    :type cl:string
    :initform "")
   (transcript
    :reader transcript
    :initarg :transcript
    :type cl:string
    :initform "")
   (raw_result
    :reader raw_result
    :initarg :raw_result
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

(cl:defclass ExtractKeyword-response (<ExtractKeyword-response>)
  ())

(cl:defmethod cl:initialize-instance :after ((m <ExtractKeyword-response>) cl:&rest args)
  (cl:declare (cl:ignorable args))
  (cl:unless (cl:typep m 'ExtractKeyword-response)
    (roslisp-msg-protocol:msg-deprecation-warning "using old message class name voice_keyword_extractor-srv:<ExtractKeyword-response> is deprecated: use voice_keyword_extractor-srv:ExtractKeyword-response instead.")))

(cl:ensure-generic-function 'success-val :lambda-list '(m))
(cl:defmethod success-val ((m <ExtractKeyword-response>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader voice_keyword_extractor-srv:success-val is deprecated.  Use voice_keyword_extractor-srv:success instead.")
  (success m))

(cl:ensure-generic-function 'keyword-val :lambda-list '(m))
(cl:defmethod keyword-val ((m <ExtractKeyword-response>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader voice_keyword_extractor-srv:keyword-val is deprecated.  Use voice_keyword_extractor-srv:keyword instead.")
  (keyword m))

(cl:ensure-generic-function 'transcript-val :lambda-list '(m))
(cl:defmethod transcript-val ((m <ExtractKeyword-response>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader voice_keyword_extractor-srv:transcript-val is deprecated.  Use voice_keyword_extractor-srv:transcript instead.")
  (transcript m))

(cl:ensure-generic-function 'raw_result-val :lambda-list '(m))
(cl:defmethod raw_result-val ((m <ExtractKeyword-response>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader voice_keyword_extractor-srv:raw_result-val is deprecated.  Use voice_keyword_extractor-srv:raw_result instead.")
  (raw_result m))

(cl:ensure-generic-function 'error_message-val :lambda-list '(m))
(cl:defmethod error_message-val ((m <ExtractKeyword-response>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader voice_keyword_extractor-srv:error_message-val is deprecated.  Use voice_keyword_extractor-srv:error_message instead.")
  (error_message m))

(cl:ensure-generic-function 'processing_time-val :lambda-list '(m))
(cl:defmethod processing_time-val ((m <ExtractKeyword-response>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader voice_keyword_extractor-srv:processing_time-val is deprecated.  Use voice_keyword_extractor-srv:processing_time instead.")
  (processing_time m))
(cl:defmethod roslisp-msg-protocol:serialize ((msg <ExtractKeyword-response>) ostream)
  "Serializes a message object of type '<ExtractKeyword-response>"
  (cl:write-byte (cl:ldb (cl:byte 8 0) (cl:if (cl:slot-value msg 'success) 1 0)) ostream)
  (cl:let ((__ros_str_len (cl:length (cl:slot-value msg 'keyword))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) __ros_str_len) ostream))
  (cl:map cl:nil #'(cl:lambda (c) (cl:write-byte (cl:char-code c) ostream)) (cl:slot-value msg 'keyword))
  (cl:let ((__ros_str_len (cl:length (cl:slot-value msg 'transcript))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) __ros_str_len) ostream))
  (cl:map cl:nil #'(cl:lambda (c) (cl:write-byte (cl:char-code c) ostream)) (cl:slot-value msg 'transcript))
  (cl:let ((__ros_str_len (cl:length (cl:slot-value msg 'raw_result))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) __ros_str_len) ostream))
  (cl:map cl:nil #'(cl:lambda (c) (cl:write-byte (cl:char-code c) ostream)) (cl:slot-value msg 'raw_result))
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
(cl:defmethod roslisp-msg-protocol:deserialize ((msg <ExtractKeyword-response>) istream)
  "Deserializes a message object of type '<ExtractKeyword-response>"
    (cl:setf (cl:slot-value msg 'success) (cl:not (cl:zerop (cl:read-byte istream))))
    (cl:let ((__ros_str_len 0))
      (cl:setf (cl:ldb (cl:byte 8 0) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:slot-value msg 'keyword) (cl:make-string __ros_str_len))
      (cl:dotimes (__ros_str_idx __ros_str_len msg)
        (cl:setf (cl:char (cl:slot-value msg 'keyword) __ros_str_idx) (cl:code-char (cl:read-byte istream)))))
    (cl:let ((__ros_str_len 0))
      (cl:setf (cl:ldb (cl:byte 8 0) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:slot-value msg 'transcript) (cl:make-string __ros_str_len))
      (cl:dotimes (__ros_str_idx __ros_str_len msg)
        (cl:setf (cl:char (cl:slot-value msg 'transcript) __ros_str_idx) (cl:code-char (cl:read-byte istream)))))
    (cl:let ((__ros_str_len 0))
      (cl:setf (cl:ldb (cl:byte 8 0) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:slot-value msg 'raw_result) (cl:make-string __ros_str_len))
      (cl:dotimes (__ros_str_idx __ros_str_len msg)
        (cl:setf (cl:char (cl:slot-value msg 'raw_result) __ros_str_idx) (cl:code-char (cl:read-byte istream)))))
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
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql '<ExtractKeyword-response>)))
  "Returns string type for a service object of type '<ExtractKeyword-response>"
  "voice_keyword_extractor/ExtractKeywordResponse")
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql 'ExtractKeyword-response)))
  "Returns string type for a service object of type 'ExtractKeyword-response"
  "voice_keyword_extractor/ExtractKeywordResponse")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql '<ExtractKeyword-response>)))
  "Returns md5sum for a message object of type '<ExtractKeyword-response>"
  "e6ee6cf4f2ad6072c8d07a6cc7a7b46a")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql 'ExtractKeyword-response)))
  "Returns md5sum for a message object of type 'ExtractKeyword-response"
  "e6ee6cf4f2ad6072c8d07a6cc7a7b46a")
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql '<ExtractKeyword-response>)))
  "Returns full string definition for message of type '<ExtractKeyword-response>"
  (cl:format cl:nil "bool success~%string keyword~%string transcript~%string raw_result~%string error_message~%float32 processing_time~%~%~%~%"))
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql 'ExtractKeyword-response)))
  "Returns full string definition for message of type 'ExtractKeyword-response"
  (cl:format cl:nil "bool success~%string keyword~%string transcript~%string raw_result~%string error_message~%float32 processing_time~%~%~%~%"))
(cl:defmethod roslisp-msg-protocol:serialization-length ((msg <ExtractKeyword-response>))
  (cl:+ 0
     1
     4 (cl:length (cl:slot-value msg 'keyword))
     4 (cl:length (cl:slot-value msg 'transcript))
     4 (cl:length (cl:slot-value msg 'raw_result))
     4 (cl:length (cl:slot-value msg 'error_message))
     4
))
(cl:defmethod roslisp-msg-protocol:ros-message-to-list ((msg <ExtractKeyword-response>))
  "Converts a ROS message object to a list"
  (cl:list 'ExtractKeyword-response
    (cl:cons ':success (success msg))
    (cl:cons ':keyword (keyword msg))
    (cl:cons ':transcript (transcript msg))
    (cl:cons ':raw_result (raw_result msg))
    (cl:cons ':error_message (error_message msg))
    (cl:cons ':processing_time (processing_time msg))
))
(cl:defmethod roslisp-msg-protocol:service-request-type ((msg (cl:eql 'ExtractKeyword)))
  'ExtractKeyword-request)
(cl:defmethod roslisp-msg-protocol:service-response-type ((msg (cl:eql 'ExtractKeyword)))
  'ExtractKeyword-response)
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql 'ExtractKeyword)))
  "Returns string type for a service object of type '<ExtractKeyword>"
  "voice_keyword_extractor/ExtractKeyword")