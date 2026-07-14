// Auto-generated. Do not edit!

// (in-package voice_keyword_extractor.srv)


"use strict";

const _serializer = _ros_msg_utils.Serialize;
const _arraySerializer = _serializer.Array;
const _deserializer = _ros_msg_utils.Deserialize;
const _arrayDeserializer = _deserializer.Array;
const _finder = _ros_msg_utils.Find;
const _getByteLength = _ros_msg_utils.getByteLength;

//-----------------------------------------------------------


//-----------------------------------------------------------

class ExtractKeywordRequest {
  constructor(initObj={}) {
    if (initObj === null) {
      // initObj === null is a special case for deserialization where we don't initialize fields
      this.start_recording = null;
      this.record_seconds = null;
    }
    else {
      if (initObj.hasOwnProperty('start_recording')) {
        this.start_recording = initObj.start_recording
      }
      else {
        this.start_recording = false;
      }
      if (initObj.hasOwnProperty('record_seconds')) {
        this.record_seconds = initObj.record_seconds
      }
      else {
        this.record_seconds = 0.0;
      }
    }
  }

  static serialize(obj, buffer, bufferOffset) {
    // Serializes a message object of type ExtractKeywordRequest
    // Serialize message field [start_recording]
    bufferOffset = _serializer.bool(obj.start_recording, buffer, bufferOffset);
    // Serialize message field [record_seconds]
    bufferOffset = _serializer.float32(obj.record_seconds, buffer, bufferOffset);
    return bufferOffset;
  }

  static deserialize(buffer, bufferOffset=[0]) {
    //deserializes a message object of type ExtractKeywordRequest
    let len;
    let data = new ExtractKeywordRequest(null);
    // Deserialize message field [start_recording]
    data.start_recording = _deserializer.bool(buffer, bufferOffset);
    // Deserialize message field [record_seconds]
    data.record_seconds = _deserializer.float32(buffer, bufferOffset);
    return data;
  }

  static getMessageSize(object) {
    return 5;
  }

  static datatype() {
    // Returns string type for a service object
    return 'voice_keyword_extractor/ExtractKeywordRequest';
  }

  static md5sum() {
    //Returns md5sum for a message object
    return 'ddabba50df5d9f6300be64daba5e3cb6';
  }

  static messageDefinition() {
    // Returns full string definition for message
    return `
    bool start_recording
    float32 record_seconds
    
    `;
  }

  static Resolve(msg) {
    // deep-construct a valid message object instance of whatever was passed in
    if (typeof msg !== 'object' || msg === null) {
      msg = {};
    }
    const resolved = new ExtractKeywordRequest(null);
    if (msg.start_recording !== undefined) {
      resolved.start_recording = msg.start_recording;
    }
    else {
      resolved.start_recording = false
    }

    if (msg.record_seconds !== undefined) {
      resolved.record_seconds = msg.record_seconds;
    }
    else {
      resolved.record_seconds = 0.0
    }

    return resolved;
    }
};

class ExtractKeywordResponse {
  constructor(initObj={}) {
    if (initObj === null) {
      // initObj === null is a special case for deserialization where we don't initialize fields
      this.success = null;
      this.keyword = null;
      this.transcript = null;
      this.raw_result = null;
      this.error_message = null;
      this.processing_time = null;
    }
    else {
      if (initObj.hasOwnProperty('success')) {
        this.success = initObj.success
      }
      else {
        this.success = false;
      }
      if (initObj.hasOwnProperty('keyword')) {
        this.keyword = initObj.keyword
      }
      else {
        this.keyword = '';
      }
      if (initObj.hasOwnProperty('transcript')) {
        this.transcript = initObj.transcript
      }
      else {
        this.transcript = '';
      }
      if (initObj.hasOwnProperty('raw_result')) {
        this.raw_result = initObj.raw_result
      }
      else {
        this.raw_result = '';
      }
      if (initObj.hasOwnProperty('error_message')) {
        this.error_message = initObj.error_message
      }
      else {
        this.error_message = '';
      }
      if (initObj.hasOwnProperty('processing_time')) {
        this.processing_time = initObj.processing_time
      }
      else {
        this.processing_time = 0.0;
      }
    }
  }

  static serialize(obj, buffer, bufferOffset) {
    // Serializes a message object of type ExtractKeywordResponse
    // Serialize message field [success]
    bufferOffset = _serializer.bool(obj.success, buffer, bufferOffset);
    // Serialize message field [keyword]
    bufferOffset = _serializer.string(obj.keyword, buffer, bufferOffset);
    // Serialize message field [transcript]
    bufferOffset = _serializer.string(obj.transcript, buffer, bufferOffset);
    // Serialize message field [raw_result]
    bufferOffset = _serializer.string(obj.raw_result, buffer, bufferOffset);
    // Serialize message field [error_message]
    bufferOffset = _serializer.string(obj.error_message, buffer, bufferOffset);
    // Serialize message field [processing_time]
    bufferOffset = _serializer.float32(obj.processing_time, buffer, bufferOffset);
    return bufferOffset;
  }

  static deserialize(buffer, bufferOffset=[0]) {
    //deserializes a message object of type ExtractKeywordResponse
    let len;
    let data = new ExtractKeywordResponse(null);
    // Deserialize message field [success]
    data.success = _deserializer.bool(buffer, bufferOffset);
    // Deserialize message field [keyword]
    data.keyword = _deserializer.string(buffer, bufferOffset);
    // Deserialize message field [transcript]
    data.transcript = _deserializer.string(buffer, bufferOffset);
    // Deserialize message field [raw_result]
    data.raw_result = _deserializer.string(buffer, bufferOffset);
    // Deserialize message field [error_message]
    data.error_message = _deserializer.string(buffer, bufferOffset);
    // Deserialize message field [processing_time]
    data.processing_time = _deserializer.float32(buffer, bufferOffset);
    return data;
  }

  static getMessageSize(object) {
    let length = 0;
    length += _getByteLength(object.keyword);
    length += _getByteLength(object.transcript);
    length += _getByteLength(object.raw_result);
    length += _getByteLength(object.error_message);
    return length + 21;
  }

  static datatype() {
    // Returns string type for a service object
    return 'voice_keyword_extractor/ExtractKeywordResponse';
  }

  static md5sum() {
    //Returns md5sum for a message object
    return '915e1fc7f313a415f88e5f75730c00e5';
  }

  static messageDefinition() {
    // Returns full string definition for message
    return `
    bool success
    string keyword
    string transcript
    string raw_result
    string error_message
    float32 processing_time
    
    
    `;
  }

  static Resolve(msg) {
    // deep-construct a valid message object instance of whatever was passed in
    if (typeof msg !== 'object' || msg === null) {
      msg = {};
    }
    const resolved = new ExtractKeywordResponse(null);
    if (msg.success !== undefined) {
      resolved.success = msg.success;
    }
    else {
      resolved.success = false
    }

    if (msg.keyword !== undefined) {
      resolved.keyword = msg.keyword;
    }
    else {
      resolved.keyword = ''
    }

    if (msg.transcript !== undefined) {
      resolved.transcript = msg.transcript;
    }
    else {
      resolved.transcript = ''
    }

    if (msg.raw_result !== undefined) {
      resolved.raw_result = msg.raw_result;
    }
    else {
      resolved.raw_result = ''
    }

    if (msg.error_message !== undefined) {
      resolved.error_message = msg.error_message;
    }
    else {
      resolved.error_message = ''
    }

    if (msg.processing_time !== undefined) {
      resolved.processing_time = msg.processing_time;
    }
    else {
      resolved.processing_time = 0.0
    }

    return resolved;
    }
};

module.exports = {
  Request: ExtractKeywordRequest,
  Response: ExtractKeywordResponse,
  md5sum() { return 'e6ee6cf4f2ad6072c8d07a6cc7a7b46a'; },
  datatype() { return 'voice_keyword_extractor/ExtractKeyword'; }
};
