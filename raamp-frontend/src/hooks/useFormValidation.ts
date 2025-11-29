/**
 * Reusable form validation hook with inline error messages
 */

import { useState, useCallback } from 'react';

export interface ValidationRule {
  required?: boolean | string;
  minLength?: { value: number; message: string };
  maxLength?: { value: number; message: string };
  pattern?: { value: RegExp; message: string };
  validate?: (value: unknown) => string | boolean;
}

export interface FieldConfig {
  [key: string]: ValidationRule;
}

export interface TouchedFields {
  [key: string]: boolean;
}

export interface FormErrors {
  [key: string]: string;
}

export interface UseFormValidationReturn<T> {
  errors: FormErrors;
  touched: TouchedFields;
  validateField: (name: string, value: unknown) => string;
  validateForm: (values: T) => boolean;
  touchField: (name: string) => void;
  touchAllFields: () => void;
  resetValidation: () => void;
  isFieldValid: (name: string) => boolean;
  getFieldError: (name: string) => string;
}

export function useFormValidation<T extends Record<string, unknown>>(
  validationRules: FieldConfig
): UseFormValidationReturn<T> {
  const [touched, setTouched] = useState<TouchedFields>({});
  const [errors, setErrors] = useState<FormErrors>({});

  const validateField = useCallback(
    (name: string, value: unknown): string => {
      const rules = validationRules[name];
      if (!rules) return '';

      // Required validation
      if (rules.required) {
        const isEmpty =
          value === null ||
          value === undefined ||
          (typeof value === 'string' && value.trim() === '') ||
          (Array.isArray(value) && value.length === 0);

        if (isEmpty) {
          return typeof rules.required === 'string'
            ? rules.required
            : 'This field is required';
        }
      }

      const stringValue = String(value || '');

      // MinLength validation
      if (rules.minLength && stringValue.length < rules.minLength.value) {
        return rules.minLength.message;
      }

      // MaxLength validation
      if (rules.maxLength && stringValue.length > rules.maxLength.value) {
        return rules.maxLength.message;
      }

      // Pattern validation
      if (rules.pattern && !rules.pattern.value.test(stringValue)) {
        return rules.pattern.message;
      }

      // Custom validation
      if (rules.validate) {
        const result = rules.validate(value);
        if (typeof result === 'string') return result;
        if (result === false) return 'Invalid value';
      }

      return '';
    },
    [validationRules]
  );

  const validateForm = useCallback(
    (values: T): boolean => {
      const newErrors: FormErrors = {};
      let isValid = true;

      Object.keys(validationRules).forEach((fieldName) => {
        const error = validateField(fieldName, values[fieldName]);
        if (error) {
          newErrors[fieldName] = error;
          isValid = false;
        }
      });

      setErrors(newErrors);
      return isValid;
    },
    [validateField, validationRules]
  );

  const touchField = useCallback((name: string) => {
    setTouched((prev) => ({ ...prev, [name]: true }));
  }, []);

  const touchAllFields = useCallback(() => {
    const allFields = Object.keys(validationRules).reduce(
      (acc, key) => ({ ...acc, [key]: true }),
      {}
    );
    setTouched(allFields);
  }, [validationRules]);

  const resetValidation = useCallback(() => {
    setTouched({});
    setErrors({});
  }, []);

  const isFieldValid = useCallback(
    (name: string): boolean => {
      return !errors[name] || !touched[name];
    },
    [errors, touched]
  );

  const getFieldError = useCallback(
    (name: string): string => {
      return touched[name] ? errors[name] || '' : '';
    },
    [errors, touched]
  );

  return {
    errors,
    touched,
    validateField,
    validateForm,
    touchField,
    touchAllFields,
    resetValidation,
    isFieldValid,
    getFieldError,
  };
}
