"use client"
import { useEffect, useRef, useState } from "react"
import { InputGroup,InputGroupTextarea,InputGroupAddon,InputGroupButton,InputGroupText } from "@/components/ui/input-group"
import { Separator } from "@/components/ui/separator"
import { ArrowUpIcon } from "lucide-react"
import { IconCheck, IconInfoCircle, IconPlus } from "@tabler/icons-react"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"

function TextBox({messages,setMessages,sendMessage,userId,file_names,setFileNames,setLoadingProcess,setShowHome,setShowAlert,setAlertText,setAlertTitle}){
    const [input_text,setInput_Text] = useState("") 
    const [file,setFile] = useState("")
    const [fileName,setFileName] = useState("")
    const fileInputRef = useRef(null)
     const handleUpload = async (sel_file)=>{
        if(!sel_file){
            setAlertText("Select a pdf to start conversation")
            setAlertTitle("File Error")
            setShowAlert(true)
            return
        }

        const formData = new FormData()
        formData.append('file',sel_file)

        await fetch(`http://127.0.0.1:8000/upload/?user_id=${userId}`,{
            method:"POST",
            body:formData
        }).then(res=>res.json())
        .catch(err => console.log(err))
    }

  const handleFileChange = async (e) => {
  const selectedFile = e.target.files[0];
  if (!selectedFile){
    return
  }
  if(file_names.includes(selectedFile.name)){
    setAlertText("File Already Exists")
    setAlertTitle("File Error")
    setShowAlert(true)
    return 
  }
  setFile(selectedFile)
  setFileName(selectedFile.name);
  setFileNames(prev=>[...prev,selectedFile.name])
  await handleUpload(selectedFile); 
};

const handlePlusClick = ()=>{
    if(fileInputRef.current){
        fileInputRef.current.click()
    }
}

    const onChangeHandler = async (e)=>{
      
        e.preventDefault()
        e.stopPropagation()
        let value = e.key
        if(value === "Enter" ){
          if(file_names.length <=0){
            setAlertText("No Files Uploaded")
            setAlertTitle("File Error")
            setShowAlert(true)
            return
          }  
          if(!input_text ){
              setAlertText("Query cannot be empty")
              setAlertTitle("NullQueryError")
              setShowAlert(true)
              return
            }
          if(!fileName){
            setAlertText("Select a File to start Conversation")
            setAlertTitle("File Error")
            setShowAlert(true)
            return
          }
            setShowHome(false)
            setLoadingProcess(0)
            setInput_Text("")
            sendMessage({data:input_text,type:"query",pdf:fileName})
            setMessages(prev=>[...prev,{id:Date.now(),query:input_text},])
        }
        else if(value.length == 1 ){
            setInput_Text(prev=>`${prev}${value}`)
        }
        else if(value === 'Tab'){
            setInput_Text(prev => prev+'\t')
        }
        else if(value === "Backspace"){
            setInput_Text(prev => prev.slice(0,-1))
        }
    }

    const onFileChangeHandler = (selectedfile)=>{
      setFileName(selectedfile)
    }
    return (
        <InputGroup className={'fixed bottom-2 bg-gray-900 left-1/2 transform -translate-x-1/2 w-1/2'} >
            <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileChange}
        className="hidden"
      />
        <InputGroupTextarea value={input_text} className={'text-blue-50 '} placeholder="Ask, Search or Chat..." onChange={()=>{}}  onKeyDown={onChangeHandler}/>
        <InputGroupAddon align="block-end">
          <InputGroupButton
            variant="outline"
            className="rounded-full"
            size="icon-xs"
            onClick={handlePlusClick}
          >
            <IconPlus/>
            
          </InputGroupButton>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <InputGroupButton variant="ghost" className={`text-amber-100`}>{fileName || "Select File"}</InputGroupButton>
            </DropdownMenuTrigger>
            <DropdownMenuContent
              side="top"
              align="start"
              className="[--radius:0.95rem]"
            >
              {
                file_names.length > 0 ?
                file_names.map(file=>{
                  return <DropdownMenuItem key={Date.now()} onClick={()=> onFileChangeHandler(file)}>{file}</DropdownMenuItem>
                }) :<DropdownMenuItem disabled>No files uploaded</DropdownMenuItem>
    
              }
            </DropdownMenuContent>
          </DropdownMenu>
          <InputGroupText className="ml-auto"></InputGroupText>
          <Separator orientation="vertical" className="!h-4" />
          <InputGroupButton
            variant="default"
            className="rounded-full p-0 m-0"
            size="icon-xs"
            disabled={1 == 2}
          >
            <ArrowUpIcon 
            />
            <span className="sr-only">Send</span>
          </InputGroupButton>
        </InputGroupAddon>
      </InputGroup>
    )
}

export default TextBox