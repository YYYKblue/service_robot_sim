
(cl:in-package :asdf)

(defsystem "cloud_tts-srv"
  :depends-on (:roslisp-msg-protocol :roslisp-utils )
  :components ((:file "_package")
    (:file "SynthesizeSpeech" :depends-on ("_package_SynthesizeSpeech"))
    (:file "_package_SynthesizeSpeech" :depends-on ("_package"))
  ))