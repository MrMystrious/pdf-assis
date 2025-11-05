"use client";
import { useEffect } from "react";
import { AlertCircleIcon, CheckCircle2Icon } from "lucide-react";
import {
  Alert,
  AlertDescription,
  AlertTitle,
} from "@/components/ui/alert";

export default function AlertDia({ title, text, showAlert, setShowAlert, duration = 3000 }) {
  useEffect(() => {
    if (showAlert) {
      const timer = setTimeout(() => {
        setShowAlert(false);
      }, duration);
      return () => clearTimeout(timer);
    }
  }, [showAlert, setShowAlert, duration]);

  if (!showAlert) return null;

  return (
    <div className="w-full p-6 flex justify-center animate-fade-in">
      <div className="w-full max-w-lg">
        <Alert className="border-blue-400 bg-blue-50 text-blue-900 shadow-lg">
          <CheckCircle2Icon className="text-blue-600" />
          <AlertTitle className="font-semibold">{title}</AlertTitle>
          <AlertDescription>{text}</AlertDescription>
        </Alert>
      </div>
    </div>
  );
}
