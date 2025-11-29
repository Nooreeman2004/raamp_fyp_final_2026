/**
 * Reusable form field component with inline validation
 */

import { ReactNode } from "react";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { cn } from "@/lib/utils";
import { AlertCircle, CheckCircle2 } from "lucide-react";

interface FormFieldProps {
  label: string;
  name: string;
  type?: 'text' | 'email' | 'password' | 'tel' | 'number' | 'textarea' | 'select';
  value: string;
  onChange: (value: string) => void;
  onBlur?: () => void;
  error?: string;
  touched?: boolean;
  required?: boolean;
  placeholder?: string;
  disabled?: boolean;
  helperText?: string;
  options?: Array<{ value: string; label: string }>;
  rows?: number;
  maxLength?: number;
  showValidation?: boolean;
  icon?: ReactNode;
  className?: string;
}

export default function FormField({
  label,
  name,
  type = 'text',
  value,
  onChange,
  onBlur,
  error,
  touched = false,
  required = false,
  placeholder,
  disabled = false,
  helperText,
  options = [],
  rows = 3,
  maxLength,
  showValidation = true,
  icon,
  className,
}: FormFieldProps) {
  const hasError = touched && error;
  const isValid = touched && !error && value;

  return (
    <div className={cn("space-y-2", className)}>
      <div className="flex items-center justify-between">
        <Label htmlFor={name} className="text-sm font-medium">
          {label}
          {required && <span className="text-destructive ml-1">*</span>}
        </Label>
        {maxLength && value && (
          <span className="text-xs text-muted-foreground">
            {value.length}/{maxLength}
          </span>
        )}
      </div>

      <div className="relative">
        {icon && (
          <div className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground">
            {icon}
          </div>
        )}

        {type === 'textarea' ? (
          <Textarea
            id={name}
            name={name}
            value={value}
            onChange={(e) => onChange(e.target.value)}
            onBlur={onBlur}
            placeholder={placeholder}
            disabled={disabled}
            rows={rows}
            maxLength={maxLength}
            className={cn(
              "resize-none",
              hasError && "border-destructive focus-visible:ring-destructive",
              isValid && showValidation && "border-green-500 focus-visible:ring-green-500"
            )}
          />
        ) : type === 'select' ? (
          <Select value={value} onValueChange={onChange} disabled={disabled}>
            <SelectTrigger
              id={name}
              className={cn(
                hasError && "border-destructive focus-visible:ring-destructive",
                isValid && showValidation && "border-green-500 focus-visible:ring-green-500"
              )}
              onBlur={onBlur}
            >
              <SelectValue placeholder={placeholder || `Select ${label.toLowerCase()}`} />
            </SelectTrigger>
            <SelectContent>
              {options.map((option) => (
                <SelectItem key={option.value} value={option.value}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        ) : (
          <Input
            id={name}
            name={name}
            type={type}
            value={value}
            onChange={(e) => onChange(e.target.value)}
            onBlur={onBlur}
            placeholder={placeholder}
            disabled={disabled}
            maxLength={maxLength}
            className={cn(
              icon && "pl-10",
              hasError && "border-destructive focus-visible:ring-destructive",
              isValid && showValidation && "border-green-500 focus-visible:ring-green-500"
            )}
          />
        )}

        {showValidation && touched && (
          <div className="absolute right-3 top-1/2 -translate-y-1/2">
            {hasError ? (
              <AlertCircle className="h-4 w-4 text-destructive" />
            ) : isValid ? (
              <CheckCircle2 className="h-4 w-4 text-green-500" />
            ) : null}
          </div>
        )}
      </div>

      {/* Helper text or error message */}
      {hasError ? (
        <p className="text-sm text-destructive flex items-center gap-1">
          <AlertCircle className="h-3 w-3" />
          {error}
        </p>
      ) : helperText ? (
        <p className="text-sm text-muted-foreground">{helperText}</p>
      ) : null}
    </div>
  );
}
