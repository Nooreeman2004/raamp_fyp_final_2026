
import { useState, useEffect } from "react";

/**
 * A hook to persist form state in sessionStorage.
 * 
 * @param key The unique key for the storage item.
 * @param initialValues The initial values of the form.
 * @returns [values, handleChange, setValues, clearPersistence]
 */
export const useFormPersistence = <T>(key: string, initialValues: T) => {
    // Initialize state with stored value or initialValue
    const [values, setValues] = useState<T>(() => {
        try {
            const item = sessionStorage.getItem(key);
            return item ? JSON.parse(item) : initialValues;
        } catch (error) {
            console.error(`Error reading sessionStorage key "${key}":`, error);
            return initialValues;
        }
    });

    // Update sessionStorage whenever values change
    useEffect(() => {
        try {
            sessionStorage.setItem(key, JSON.stringify(values));
        } catch (error) {
            console.error(`Error saving sessionStorage key "${key}":`, error);
        }
    }, [key, values]);

    // Helper to handle standard input changes
    const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
        const { name, value } = e.target;
        setValues((prev) => ({ ...prev, [name]: value }));
    };

    // Helper to clear storage (e.g. on successful submit)
    const clearPersistence = () => {
        try {
            sessionStorage.removeItem(key);
        } catch (error) {
            console.error(`Error clearing sessionStorage key "${key}":`, error);
        }
    };

    return { values, setValues, handleChange, clearPersistence };
};
