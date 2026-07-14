
(cl:in-package :asdf)

(defsystem "voice_keyword_extractor-srv"
  :depends-on (:roslisp-msg-protocol :roslisp-utils )
  :components ((:file "_package")
    (:file "ExtractKeyword" :depends-on ("_package_ExtractKeyword"))
    (:file "_package_ExtractKeyword" :depends-on ("_package"))
  ))