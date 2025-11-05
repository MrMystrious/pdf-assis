"use client"
import TextBox from "./page-components/textBox"
import { useState, useEffect } from "react"
import Query from "./page-components/query"
import { v4 as uuidv4 } from "uuid"
import { Progress } from "@/components/ui/progress"
import TypingText from "@/components/ui/shadcn-io/typing-text"
import AlertDia from "./page-components/alert"

export default function Home() {
  const [socket, setSocket] = useState(null)
  const [messages, setMessages] = useState([])
  const [userId, setUserId] = useState(uuidv4())
  const [file_names, setFileNames] = useState([])
  const [progress, setProgress] = useState(0)
  const [loading, setLoading] = useState(false)
  const [loadingProcess, setLoadingProcess] = useState(0)
  const [showHome,setShowHome] = useState(true)
  const [showAlert,setShowAlert] = useState(false)
  const [alertText,setAlertText] = useState("text")
  const [alertTitle,setAlertTitle] = useState("title")

  const words = ["Simple","Conversational Intelligence","LLM-Powered Reasoning","Streaming Mind Engine","Dynamic AI Memory","Stateful Conversations"]
  
  useEffect(() => {
    const ws = new WebSocket(`ws://127.0.0.1:8000/ws/${userId}`)
    ws.onopen = () => console.log("Connected as ", userId)
    ws.onmessage = (e) => handleMessage(e)
    ws.onclose = () => console.log("Disconnected")

    setSocket(ws)

    return () => ws.close()
  }, [userId])

  function handleMessage(event) {
    const data = JSON.parse(event.data)
    const res = data.response
    const type = data.type

    if (type === "query") {
      if (loadingProcess < 100) setLoadingProcess(100)

      setMessages((prev) => {
        const updated = [...prev]
        updated[updated.length - 1] = {
          ...updated[updated.length - 1],
          response: (updated[updated.length - 1].response || "") + res,
        }
        return updated
      })
    } else if (type == "uploadStatus") {
      setLoading(true)
      setProgress((prev) => prev + 16.7)
    } else if (type == "uploadEnd") {
      setProgress(100)
      setLoading(false)
      setProgress(0)
    } else if (type == "queryProcessed") {
      setLoadingProcess((prev) => prev + 17)
    }
  }

  function sendMessage(msg) {
    if (socket && socket.readyState == WebSocket.OPEN) {
      socket.send(JSON.stringify(msg))
    }
  }

  const canLoadPage = loading
    ? "opacity-50 pointer-events-none cursor-not-allowed"
    : "opacity-100"

  const componentToLoad = loading ? (
    <div
      className="flex justify-center self-start pt-6 w-full bg-black"
      style={{
    
        display: "flex",
        justifyContent: "center",
        alignSelf: "flex-start",
        paddingTop: "1.5rem",
        width: "100%",
        fontSize: "14px",
        lineHeight: "1.5",
        letterSpacing: "normal",
      }}
    >
      <Progress value={progress} className="w-[60%] bg-gray-700 [&>div]:bg-blue-400" />
    </div>
  ) : (
    <div className={`bg-black w-full min-h-screen ${canLoadPage}`}>
      <TextBox
        messages={messages}
        setMessages={setMessages}
        sendMessage={sendMessage}
        userId={userId}
        file_names={file_names}
        setFileNames={setFileNames}
        setLoadingProcess={setLoadingProcess}
        setShowHome={setShowHome}
        setShowAlert = {setShowAlert}
        setAlertText = {setAlertText}
        setAlertTitle = {setAlertTitle}
      />
       {
        showHome ? 
        <div className="min-h-screen w-full flex items-center justify-center bg-black">
        <TypingText
          text={words}
          typingSpeed={75}
          pauseDuration={1500}
          showCursor={true}
          cursorCharacter="|"
          className="text-5xl font-extrabold text-center font-sans tracking-wide"
          textColors={['#3b82f6', '#8b5cf6', '#06b6d4']}
          variableSpeed={{ min: 50, max: 120 }}
        />
      </div>

        : 
        <Query
        messages={messages}
        loading={loading}
        setLoading={setLoading}
        loadingProcess={loadingProcess}
        setLoadingProcess={setLoadingProcess}
      />
      }
    </div>
  )

  return (
    <div className="w-full min-h-screen bg-black">
    {showAlert ? 
       <div className="absolute right-0 w-[35%]">
        <AlertDia
          title={alertText}
          text={alertTitle}
          showAlert={showAlert}
          setShowAlert = {setShowAlert}
        />
      </div> :
      <div/>

    }
    {componentToLoad}
    </div>
  )
}
