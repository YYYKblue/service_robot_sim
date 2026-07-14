// Auto-generated. Do not edit!

// (in-package cloud_tts.srv)


"use strict";

const _serializer = _ros_msg_utils.Serialize;
const _arraySerializer = _serializer.Array;
const _deserializer = _ros_msg_utils.Deserialize;
const _arrayDeserializer = _deserializer.Array;
const _finder = _ros_msg_utils.Find;
const _getByteLength = _ros_msg_utils.getByteLength;

//-----------------------------------------------------------


//-----------------------------------------------------------

class SynthesizeSpeechRequest {
  constructor(initObj={}) {
    if (initObj === null) {
      // initObj === null is a special case for deserialization where we don't initialize fields
      this.text = null;
      this.play_audio = null;
    }
    else {
      if (initObj.hasOwnProperty('text')) {
        this.text = initObj.text
      }
      else {
        this.text = '';
      }
      if (initObj.hasOwnProperty('play_audio')) {
        this.play_audio = initObj.play_audio
      }
      else {
        this.play_audio = false;
      }
    }
  }

  static serialize(obj, buffer, bufferOffset) {
    // Serializes a message object of type SynthesizeSpeechRequest
    // Serialize message field [text]
    bufferOffset = _serializer.string(obj.text, buffer, bufferOffset);
    // Serialize message field [play_audio]
    bufferOffset = _serializer.bool(obj.play_audio, buffer, bufferOffset);
    return bufferOffset;
  }

  static deserialize(buffer, bufferOffset=[0]) {
    //deserializes a message object of type SynthesizeSpeechRequest
    let len;
    let data = new SynthesizeSpeechRequest(null);
    // Deserialize message field [text]
    data.text = _deserializer.string(buffer, bufferOffset);
    // Deserialize message field [play_audio]
    data.play_audio = _deserializer.bool(buffer, bufferOffset);
    return data;
  }

  static getMessageSize(object) {
    let length = 0;
    length += _getByteLength(object.text);
    return length + 5;
  }

  static datatype() {
    // Returns string type for a service object
    return 'cloud_tts/SynthesizeSpeechRequest';
  }

  static md5sum() {
    //Returns md5sum for a message object
    return '998a49c3d49b92ef3b081db6f4fd756c';
  }

  static messageDefinition() {
    // Returns full string definition for message
    return `
    string text
    bool play_audio
    
    `;
  }

  static Resolve(msg) {
    // deep-construct a valid message object instance of whatever was passed in
    if (typeof msg !== 'object' || msg === null) {
      msg = {};
    }
    const resolved = new SynthesizeSpeechRequest(null);
    if (msg.text !== undefined) {
      resolved.text = msg.text;
    }
    else {
      resolved.text = ''
    }

    if (msg.play_audio !== undefined) {
      resolved.play_audio = msg.play_audio;
    }
    else {
      resolved.play_audio = false
    }

    return resolved;
    }
};

class SynthesizeSpeechResponse {
  constructor(initObj={}) {
    if (initObj === null) {
      // initObj === null is a special case for deserialization where we don't initialize fields
      this.success = null;
      this.audio_path = null;
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
      if (initObj.hasOwnProperty('audio_path')) {
        this.audio_path = initObj.audio_path
      }
      else {
        this.audio_path = '';
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
    // Serializes a message object of type SynthesizeSpeechResponse
    // Serialize message field [success]
    bufferOffset = _serializer.bool(obj.success, buffer, bufferOffset);
    // Serialize message field [audio_path]
    bufferOffset = _serializer.string(obj.audio_path, buffer, bufferOffset);
    // Serialize message field [error_message]
    bufferOffset = _serializer.string(obj.error_message, buffer, bufferOffset);
    // Serialize message field [processing_time]
    bufferOffset = _serializer.float32(obj.processing_time, buffer, bufferOffset);
    return bufferOffset;
  }

  static deserialize(buffer, bufferOffset=[0]) {
    //deserializes a message object of type SynthesizeSpeechResponse
    let len;
    let data = new SynthesizeSpeechResponse(null);
    // Deserialize message field [success]
    data.success = _deserializer.bool(buffer, bufferOffset);
    // Deserialize message field [audio_path]
    data.audio_path = _deserializer.string(buffer, bufferOffset);
    // Deserialize message field [error_message]
    data.error_message = _deserializer.string(buffer, bufferOffset);
    // Deserialize message field [processing_time]
    data.processing_time = _deserializer.float32(buffer, bufferOffset);
    return data;
  }

  static getMessageSize(object) {
    let length = 0;
    length += _getByteLength(object.audio_path);
    length += _getByteLength(object.error_message);
    return length + 13;
  }

  static datatype() {
    // Returns string type for a service object
    return 'cloud_tts/SynthesizeSpeechResponse';
  }

  static md5sum() {
    //Returns md5sum for a message object
    return '28b8abf06e26fa89b8f143ddc0a9c3db';
  }

  static messageDefinition() {
    // Returns full string definition for message
    return `
    bool success
    string audio_path
    string error_message
    float32 processing_time
    
    
    `;
  }

  static Resolve(msg) {
    // deep-construct a valid message object instance of whatever was passed in
    if (typeof msg !== 'object' || msg === null) {
      msg = {};
    }
    const resolved = new SynthesizeSpeechResponse(null);
    if (msg.success !== undefined) {
      resolved.success = msg.success;
    }
    else {
      resolved.success = false
    }

    if (msg.audio_path !== undefined) {
      resolved.audio_path = msg.audio_path;
    }
    else {
      resolved.audio_path = ''
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
  Request: SynthesizeSpeechRequest,
  Response: SynthesizeSpeechResponse,
  md5sum() { return '34da7af1fde48d1628d738c7d04b1734'; },
  datatype() { return 'cloud_tts/SynthesizeSpeech'; }
};
