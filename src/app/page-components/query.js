"use client"
import { memo, useRef, useEffect } from "react"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import rehypeHighlight from "rehype-highlight"
import "highlight.js/styles/github-dark.css" 
import CircularProgress from "@/components/ui/progress-07"

function Query({ messages , loading, setLoading,loadingProcess,setLoadingProcess}) {
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  return (
    <div className="flex flex-col items-end w-full">
      {messages.map((m) => (
        <div className="w-full flex flex-col" key={m.id}>
          <Message message={m} load={loadingProcess}/>
        </div>
      ))}
      <div ref={bottomRef} className="w-full h-32"></div>
    </div>
  )
}

const Message = memo(({ message ,load}) => {
  const hasResponse = message.response && message.response.trim() !== ""

  return (
    <div className="flex flex-col w-full">
      <div className="flex justify-end w-full">
        <div className="bg-gray-700 p-4 border border-blue-300 rounded-2xl shadow-md shadow-blue-300 my-2 text-white w-1/4 mr-[12.5%]">
          <span>{message.query}</span>
        </div>
      </div>

      {hasResponse ? (
        <div className="flex justify-start w-full">
          <div className="bg-gray-900 py-4 px-8 rounded-xl my-4 text-white w-3/4 ml-[12.5%] prose prose-invert max-w-none">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              rehypePlugins={[rehypeHighlight]}
              components={{
                h1: ({ node, ...props }) => (
                  <h1 className="text-2xl font-bold mb-3" {...props} />
                ),
                h2: ({ node, ...props }) => (
                  <h2 className="text-xl font-semibold mt-4 mb-2" {...props} />
                ),
                ul: ({ node, ...props }) => (
                  <ul className="list-disc ml-6 mb-2" {...props} />
                ),
                code: ({ node, inline, className, children, ...props }) => (
                  <code
                    className={`bg-gray-800 text-green-300 px-1 rounded ${
                      inline ? "inline-block" : "block p-2"
                    }`}
                    {...props}
                  >
                    {children}
                  </code>
                ),
              }}
            >
              {message.response}
            </ReactMarkdown>
          </div>
        </div>
      ) : (
        <div className="flex justify-start w-full ml-[12.5%] my-3">
          <CircularProgress 
            className="animate-pulse"
            value={load}
            size={50}
            strokeWidth={5}
            progressClassName={
                load < 40
                  ? "stroke-red-500"
                  : load < 80
                  ? "stroke-yellow-400"
                  : "stroke-green-500"
              }
            />
        </div>
      )}
    </div>
  )
})

export default Query
