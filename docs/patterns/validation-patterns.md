<!-- File: /docs/patterns/validation-patterns.md -->
<!-- Last Updated: 2024-12-05 -->
<!-- Status: current -->

# WAIF Framework Validation Patterns

## Overview

This document defines comprehensive input validation patterns for the WAIF framework, covering client input validation, server-side validation, sanitization, and security considerations.

## Validation Architecture

### Core Validation Principles

1. **Defense in Depth**: Validate at multiple layers (client, controller, service, database)
2. **Fail Fast**: Validate inputs as early as possible in the request cycle
3. **Clear Error Messages**: Provide specific, actionable error messages
4. **Security First**: Prevent injection attacks and malicious input
5. **Type Safety**: Ensure data types match expected formats
6. **Business Rules**: Enforce domain-specific validation rules

## Input Validation Layers

### 1. Controller-Level Validation

#### Basic Input Validation Pattern
```javascript
/**
 * Controller-Level Input Validation
 * First line of defense for HTTP requests
 */
import { ValidationError } from '../../../utils/errors.js';

export class UserController {
  /**
   * Validate user creation input
   * @param {Object} data - User data to validate
   * @throws {ValidationError} Invalid input
   * @static
   */
  static validateCreateUserInput(data) {
    const errors = [];

    // Required field validation
    if (!data) {
      throw new ValidationError('Request body is required');
    }

    // Email validation
    if (!data.email) {
      errors.push({ field: 'email', message: 'Email is required' });
    } else if (!UserController.isValidEmail(data.email)) {
      errors.push({ field: 'email', message: 'Valid email address is required' });
    }

    // Name validation
    if (!data.name) {
      errors.push({ field: 'name', message: 'Name is required' });
    } else if (typeof data.name !== 'string') {
      errors.push({ field: 'name', message: 'Name must be a string' });
    } else if (data.name.trim().length === 0) {
      errors.push({ field: 'name', message: 'Name cannot be empty' });
    } else if (data.name.length > 100) {
      errors.push({ field: 'name', message: 'Name must be less than 100 characters' });
    }

    // Password validation
    if (!data.password) {
      errors.push({ field: 'password', message: 'Password is required' });
    } else if (!UserController.isValidPassword(data.password)) {
      errors.push({ 
        field: 'password', 
        message: 'Password must be at least 8 characters with uppercase, lowercase, number, and special character' 
      });
    }

    // Age validation (optional)
    if (data.age !== undefined) {
      if (!Number.isInteger(data.age)) {
        errors.push({ field: 'age', message: 'Age must be an integer' });
      } else if (data.age < 13 || data.age > 120) {
        errors.push({ field: 'age', message: 'Age must be between 13 and 120' });
      }
    }

    // Phone validation (optional)
    if (data.phone && !UserController.isValidPhone(data.phone)) {
      errors.push({ field: 'phone', message: 'Valid phone number is required' });
    }

    // Role validation
    if (data.role) {
      const allowedRoles = ['user', 'admin', 'moderator'];
      if (!allowedRoles.includes(data.role)) {
        errors.push({ 
          field: 'role', 
          message: `Role must be one of: ${allowedRoles.join(', ')}` 
        });
      }
    }

    // Throw validation error if any errors found
    if (errors.length > 0) {
      const error = new ValidationError('Validation failed');
      error.details = errors;
      throw error;
    }
  }

  /**
   * Validate user update input
   * @param {Object} data - Update data to validate
   * @throws {ValidationError} Invalid input
   * @static
   */
  static validateUpdateUserInput(data) {
    const errors = [];

    if (!data || Object.keys(data).length === 0) {
      throw new ValidationError('At least one field is required for update');
    }

    // Validate only provided fields
    if (data.email !== undefined) {
      if (!UserController.isValidEmail(data.email)) {
        errors.push({ field: 'email', message: 'Valid email address is required' });
      }
    }

    if (data.name !== undefined) {
      if (typeof data.name !== 'string' || data.name.trim().length === 0) {
        errors.push({ field: 'name', message: 'Name must be a non-empty string' });
      } else if (data.name.length > 100) {
        errors.push({ field: 'name', message: 'Name must be less than 100 characters' });
      }
    }

    if (data.age !== undefined) {
      if (!Number.isInteger(data.age) || data.age < 13 || data.age > 120) {
        errors.push({ field: 'age', message: 'Age must be integer between 13 and 120' });
      }
    }

    if (errors.length > 0) {
      const error = new ValidationError('Validation failed');
      error.details = errors;
      throw error;
    }
  }

  // --- Validation Helper Methods ---

  /**
   * Validate email format
   * @param {string} email - Email to validate
   * @returns {boolean} Valid email
   * @static
   */
  static isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email) && email.length <= 254;
  }

  /**
   * Validate password strength
   * @param {string} password - Password to validate
   * @returns {boolean} Valid password
   * @static
   */
  static isValidPassword(password) {
    // At least 8 characters, 1 uppercase, 1 lowercase, 1 number, 1 special char
    const passwordRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]).{8,}$/;
    return passwordRegex.test(password) && password.length <= 128;
  }

  /**
   * Validate phone number format
   * @param {string} phone - Phone to validate
   * @returns {boolean} Valid phone
   * @static
   */
  static isValidPhone(phone) {
    // International format: +1234567890 or domestic: (123) 456-7890
    const phoneRegex = /^(\+\d{1,3}[\s\-]?)?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{4}$/;
    return phoneRegex.test(phone);
  }

  /**
   * Validate MongoDB ObjectId
   * @param {string} id - ID to validate
   * @returns {boolean} Valid ObjectId
   * @static
   */
  static isValidObjectId(id) {
    return /^[0-9a-fA-F]{24}$/.test(id);
  }

  /**
   * Validate URL format
   * @param {string} url - URL to validate
   * @returns {boolean} Valid URL
   * @static
   */
  static isValidUrl(url) {
    try {
      const urlObj = new URL(url);
      return ['http:', 'https:'].includes(urlObj.protocol);
    } catch {
      return false;
    }
  }

  /**
   * Validate date string
   * @param {string} dateStr - Date string to validate
   * @returns {boolean} Valid date
   * @static
   */
  static isValidDate(dateStr) {
    const date = new Date(dateStr);
    return date instanceof Date && !isNaN(date.getTime());
  }
}
```

### 2. Middleware-Based Validation

#### Reusable Validation Middleware
```javascript
/**
 * Validation Middleware Pattern
 * Reusable validation functions for common scenarios
 */
import { ValidationError } from '../../../utils/errors.js';

export class ValidationMiddleware {
  /**
   * Create validation middleware for request body
   * @param {Function} validator - Validation function
   * @returns {Function} Express middleware
   */
  static validateBody(validator) {
    return (req, res, next) => {
      try {
        validator(req.body);
        next();
      } catch (error) {
        next(error);
      }
    };
  }

  /**
   * Create validation middleware for query parameters
   * @param {Function} validator - Validation function
   * @returns {Function} Express middleware
   */
  static validateQuery(validator) {
    return (req, res, next) => {
      try {
        validator(req.query);
        next();
      } catch (error) {
        next(error);
      }
    };
  }

  /**
   * Create validation middleware for path parameters
   * @param {Function} validator - Validation function
   * @returns {Function} Express middleware
   */
  static validateParams(validator) {
    return (req, res, next) => {
      try {
        validator(req.params);
        next();
      } catch (error) {
        next(error);
      }
    };
  }

  /**
   * Validate MongoDB ObjectId parameter
   * @param {string} paramName - Parameter name to validate
   * @returns {Function} Express middleware
   */
  static validateObjectId(paramName = 'id') {
    return (req, res, next) => {
      const id = req.params[paramName];
      
      if (!id || !/^[0-9a-fA-F]{24}$/.test(id)) {
        return next(new ValidationError(`Valid ${paramName} is required`, paramName));
      }
      
      next();
    };
  }

  /**
   * Validate pagination parameters
   * @returns {Function} Express middleware
   */
  static validatePagination() {
    return (req, res, next) => {
      const { page, limit } = req.query;
      
      if (page !== undefined) {
        const pageNum = parseInt(page, 10);
        if (isNaN(pageNum) || pageNum < 1) {
          return next(new ValidationError('Page must be positive integer', 'page'));
        }
        req.query.page = pageNum;
      }
      
      if (limit !== undefined) {
        const limitNum = parseInt(limit, 10);
        if (isNaN(limitNum) || limitNum < 1 || limitNum > 100) {
          return next(new ValidationError('Limit must be integer between 1 and 100', 'limit'));
        }
        req.query.limit = limitNum;
      }
      
      next();
    };
  }

  /**
   * Validate file upload parameters
   * @param {Object} options - Validation options
   * @returns {Function} Express middleware
   */
  static validateFileUpload(options = {}) {
    const {
      required = true,
      allowedTypes = ['image/jpeg', 'image/png', 'image/gif'],
      maxSize = 5 * 1024 * 1024 // 5MB
    } = options;

    return (req, res, next) => {
      if (required && !req.file) {
        return next(new ValidationError('File is required', 'file'));
      }

      if (req.file) {
        // Validate file type
        if (!allowedTypes.includes(req.file.mimetype)) {
          return next(new ValidationError(
            `File type not allowed. Allowed types: ${allowedTypes.join(', ')}`,
            'file'
          ));
        }

        // Validate file size
        if (req.file.size > maxSize) {
          return next(new ValidationError(
            `File size too large. Maximum size: ${Math.round(maxSize / 1024 / 1024)}MB`,
            'file'
          ));
        }

        // Validate file name
        if (!req.file.originalname || req.file.originalname.length > 255) {
          return next(new ValidationError('Invalid file name', 'file'));
        }

        // Check for malicious file names
        const dangerousPatterns = ['../', '.\\', '<script', '<?php', '.exe', '.bat'];
        const fileName = req.file.originalname.toLowerCase();
        if (dangerousPatterns.some(pattern => fileName.includes(pattern))) {
          return next(new ValidationError('File name contains dangerous content', 'file'));
        }
      }

      next();
    };
  }
}

// Export individual middleware functions
export const {
  validateBody,
  validateQuery, 
  validateParams,
  validateObjectId,
  validatePagination,
  validateFileUpload
} = ValidationMiddleware;
```

### 3. Schema-Based Validation

#### JSON Schema Validation Pattern
```javascript
/**
 * JSON Schema Validation Pattern
 * Using JSON Schema for complex validation rules
 */
import Ajv from 'ajv';
import addFormats from 'ajv-formats';
import { ValidationError } from '../../../utils/errors.js';

// Initialize AJV with formats
const ajv = new Ajv({ allErrors: true });
addFormats(ajv);

export class SchemaValidator {
  /**
   * User creation schema
   */
  static userCreateSchema = {
    type: 'object',
    properties: {
      name: {
        type: 'string',
        minLength: 1,
        maxLength: 100,
        pattern: '^[a-zA-Z\\s]+$'
      },
      email: {
        type: 'string',
        format: 'email',
        maxLength: 254
      },
      password: {
        type: 'string',
        minLength: 8,
        maxLength: 128,
        pattern: '^(?=.*[a-z])(?=.*[A-Z])(?=.*\\d)(?=.*[!@#$%^&*()_+\\-=\\[\\]{};\':"\\\\|,.<>\\/?]).+$'
      },
      age: {
        type: 'integer',
        minimum: 13,
        maximum: 120
      },
      phone: {
        type: 'string',
        pattern: '^(\\+\\d{1,3}[\\s\\-]?)?\\(?\\d{3}\\)?[\\s\\-]?\\d{3}[\\s\\-]?\\d{4}$'
      },
      role: {
        type: 'string',
        enum: ['user', 'admin', 'moderator']
      },
      preferences: {
        type: 'object',
        properties: {
          theme: {
            type: 'string',
            enum: ['light', 'dark', 'auto']
          },
          notifications: {
            type: 'boolean'
          },
          language: {
            type: 'string',
            pattern: '^[a-z]{2}(-[A-Z]{2})?$'
          }
        },
        additionalProperties: false
      }
    },
    required: ['name', 'email', 'password'],
    additionalProperties: false
  };

  /**
   * User update schema
   */
  static userUpdateSchema = {
    type: 'object',
    properties: {
      name: {
        type: 'string',
        minLength: 1,
        maxLength: 100
      },
      email: {
        type: 'string',
        format: 'email'
      },
      age: {
        type: 'integer',
        minimum: 13,
        maximum: 120
      },
      phone: {
        type: 'string',
        pattern: '^(\\+\\d{1,3}[\\s\\-]?)?\\(?\\d{3}\\)?[\\s\\-]?\\d{3}[\\s\\-]?\\d{4}$'
      },
      role: {
        type: 'string',
        enum: ['user', 'admin', 'moderator']
      },
      preferences: {
        type: 'object',
        properties: {
          theme: {
            type: 'string',
            enum: ['light', 'dark', 'auto']
          },
          notifications: {
            type: 'boolean'
          },
          language: {
            type: 'string',
            pattern: '^[a-z]{2}(-[A-Z]{2})?$'
          }
        },
        additionalProperties: false
      }
    },
    minProperties: 1, // At least one property required for update
    additionalProperties: false
  };

  /**
   * Create schema validation middleware
   * @param {Object} schema - JSON schema
   * @returns {Function} Express middleware
   */
  static createSchemaValidator(schema) {
    const validate = ajv.compile(schema);
    
    return (req, res, next) => {
      const valid = validate(req.body);
      
      if (!valid) {
        const errors = validate.errors.map(err => ({
          field: err.instancePath.replace('/', '') || err.params?.missingProperty || 'root',
          message: err.message,
          value: err.data
        }));
        
        const error = new ValidationError('Schema validation failed');
        error.details = errors;
        return next(error);
      }
      
      next();
    };
  }

  /**
   * Validate data against schema
   * @param {Object} data - Data to validate
   * @param {Object} schema - JSON schema
   * @throws {ValidationError} Validation failed
   */
  static validate(data, schema) {
    const validate = ajv.compile(schema);
    const valid = validate(data);
    
    if (!valid) {
      const errors = validate.errors.map(err => ({
        field: err.instancePath.replace('/', '') || err.params?.missingProperty || 'root',
        message: err.message,
        value: err.data
      }));
      
      const error = new ValidationError('Schema validation failed');
      error.details = errors;
      throw error;
    }
  }
}

// Export schema validators as middleware
export const validateUserCreate = SchemaValidator.createSchemaValidator(
  SchemaValidator.userCreateSchema
);

export const validateUserUpdate = SchemaValidator.createSchemaValidator(
  SchemaValidator.userUpdateSchema
);
```

### 4. Input Sanitization Patterns

#### Data Sanitization
```javascript
/**
 * Input Sanitization Patterns
 * Clean and normalize input data
 */
import DOMPurify from 'isomorphic-dompurify';
import validator from 'validator';

export class InputSanitizer {
  /**
   * Sanitize string input
   * @param {string} input - String to sanitize
   * @param {Object} options - Sanitization options
   * @returns {string} Sanitized string
   */
  static sanitizeString(input, options = {}) {
    if (typeof input !== 'string') {
      return input;
    }

    const {
      trim = true,
      removeHtml = true,
      normalizeWhitespace = true,
      maxLength = null
    } = options;

    let sanitized = input;

    // Trim whitespace
    if (trim) {
      sanitized = sanitized.trim();
    }

    // Remove HTML tags
    if (removeHtml) {
      sanitized = DOMPurify.sanitize(sanitized, { ALLOWED_TAGS: [] });
    }

    // Normalize whitespace
    if (normalizeWhitespace) {
      sanitized = sanitized.replace(/\s+/g, ' ');
    }

    // Truncate if needed
    if (maxLength && sanitized.length > maxLength) {
      sanitized = sanitized.substring(0, maxLength);
    }

    return sanitized;
  }

  /**
   * Sanitize email input
   * @param {string} email - Email to sanitize
   * @returns {string} Sanitized email
   */
  static sanitizeEmail(email) {
    if (typeof email !== 'string') {
      return email;
    }

    return validator.normalizeEmail(email.trim().toLowerCase(), {
      gmail_remove_dots: false,
      gmail_remove_subaddress: false,
      outlookdotcom_remove_subaddress: false,
      yahoo_remove_subaddress: false,
      icloud_remove_subaddress: false
    }) || email;
  }

  /**
   * Sanitize phone number
   * @param {string} phone - Phone to sanitize
   * @returns {string} Sanitized phone
   */
  static sanitizePhone(phone) {
    if (typeof phone !== 'string') {
      return phone;
    }

    // Remove all non-digit characters except +
    return phone.replace(/[^\d+]/g, '');
  }

  /**
   * Sanitize URL input
   * @param {string} url - URL to sanitize
   * @returns {string} Sanitized URL
   */
  static sanitizeUrl(url) {
    if (typeof url !== 'string') {
      return url;
    }

    const trimmed = url.trim();
    
    // Add protocol if missing
    if (!/^https?:\/\//i.test(trimmed)) {
      return `https://${trimmed}`;
    }
    
    return trimmed;
  }

  /**
   * Sanitize user input object
   * @param {Object} data - Data to sanitize
   * @returns {Object} Sanitized data
   */
  static sanitizeUserInput(data) {
    if (!data || typeof data !== 'object') {
      return data;
    }

    const sanitized = { ...data };

    // Sanitize string fields
    if (sanitized.name) {
      sanitized.name = this.sanitizeString(sanitized.name, { maxLength: 100 });
    }

    if (sanitized.email) {
      sanitized.email = this.sanitizeEmail(sanitized.email);
    }

    if (sanitized.phone) {
      sanitized.phone = this.sanitizePhone(sanitized.phone);
    }

    if (sanitized.website) {
      sanitized.website = this.sanitizeUrl(sanitized.website);
    }

    // Sanitize nested objects
    if (sanitized.preferences && typeof sanitized.preferences === 'object') {
      Object.keys(sanitized.preferences).forEach(key => {
        if (typeof sanitized.preferences[key] === 'string') {
          sanitized.preferences[key] = this.sanitizeString(sanitized.preferences[key]);
        }
      });
    }

    return sanitized;
  }

  /**
   * Create sanitization middleware
   * @param {Function} sanitizer - Sanitization function
   * @returns {Function} Express middleware
   */
  static createSanitizationMiddleware(sanitizer) {
    return (req, res, next) => {
      if (req.body) {
        req.body = sanitizer(req.body);
      }
      next();
    };
  }
}

// Export sanitization middleware
export const sanitizeUserInputMiddleware = InputSanitizer.createSanitizationMiddleware(
  InputSanitizer.sanitizeUserInput
);
```

## Security Validation Patterns

### SQL/NoSQL Injection Prevention
```javascript
/**
 * Injection Prevention Patterns
 */
export class SecurityValidator {
  /**
   * Validate against NoSQL injection
   * @param {any} input - Input to validate
   * @throws {ValidationError} Potential injection detected
   */
  static validateNoSQLInjection(input) {
    if (typeof input === 'object' && input !== null) {
      // Check for MongoDB operators
      const dangerousOperators = ['$where', '$regex', '$ne', '$gt', '$lt', '$in', '$nin'];
      const inputStr = JSON.stringify(input);
      
      for (const op of dangerousOperators) {
        if (inputStr.includes(op)) {
          throw new ValidationError('Potentially malicious input detected', 'security');
        }
      }
    }
  }

  /**
   * Validate against XSS attacks
   * @param {string} input - Input to validate
   * @throws {ValidationError} Potential XSS detected
   */
  static validateXSS(input) {
    if (typeof input !== 'string') {
      return;
    }

    const xssPatterns = [
      /<script[^>]*>.*?<\/script>/gi,
      /<iframe[^>]*>.*?<\/iframe>/gi,
      /javascript:/gi,
      /on\w+\s*=/gi,
      /<img[^>]+src[\s]*=[\s]*["']?[\s]*javascript:/gi
    ];

    for (const pattern of xssPatterns) {
      if (pattern.test(input)) {
        throw new ValidationError('Potentially malicious content detected', 'security');
      }
    }
  }

  /**
   * Validate file upload security
   * @param {Object} file - Uploaded file object
   * @throws {ValidationError} Security violation
   */
  static validateFileUploadSecurity(file) {
    if (!file) return;

    // Check file extension
    const dangerousExtensions = [
      '.exe', '.bat', '.cmd', '.scr', '.pif', '.com',
      '.php', '.jsp', '.asp', '.aspx', '.js', '.vbs'
    ];
    
    const fileName = file.originalname.toLowerCase();
    if (dangerousExtensions.some(ext => fileName.endsWith(ext))) {
      throw new ValidationError('File type not allowed for security reasons', 'file');
    }

    // Check for double extensions
    if ((fileName.match(/\./g) || []).length > 1) {
      const parts = fileName.split('.');
      if (parts.length > 2 && dangerousExtensions.some(ext => fileName.includes(ext))) {
        throw new ValidationError('Suspicious file name detected', 'file');
      }
    }

    // Validate MIME type matches extension
    const expectedMimeTypes = {
      '.jpg': ['image/jpeg'],
      '.jpeg': ['image/jpeg'],
      '.png': ['image/png'],
      '.gif': ['image/gif'],
      '.pdf': ['application/pdf'],
      '.txt': ['text/plain']
    };

    const ext = fileName.substring(fileName.lastIndexOf('.'));
    const expectedTypes = expectedMimeTypes[ext];
    
    if (expectedTypes && !expectedTypes.includes(file.mimetype)) {
      throw new ValidationError('File type mismatch detected', 'file');
    }
  }
}
```

## Validation Testing Patterns

### Validation Test Suite
```javascript
/**
 * Validation Testing Patterns
 */
// tests/unit/validation/user-validation.test.js
import { describe, it } from 'node:test';
import assert from 'node:assert';
import { UserController } from '../../../src/api/v1.0/controllers/user.controller.js';
import { ValidationError } from '../../../src/utils/errors.js';

describe('User Input Validation', () => {
  describe('validateCreateUserInput', () => {
    it('should pass with valid user data', () => {
      const validData = {
        name: 'John Doe',
        email: 'john@example.com',
        password: 'SecurePass123!',
        age: 25
      };

      assert.doesNotThrow(() => {
        UserController.validateCreateUserInput(validData);
      });
    });

    it('should throw ValidationError for missing required fields', () => {
      const invalidData = {
        name: 'John Doe'
        // Missing email and password
      };

      assert.throws(() => {
        UserController.validateCreateUserInput(invalidData);
      }, ValidationError);
    });

    it('should throw ValidationError for invalid email', () => {
      const invalidData = {
        name: 'John Doe',
        email: 'invalid-email',
        password: 'SecurePass123!'
      };

      assert.throws(() => {
        UserController.validateCreateUserInput(invalidData);
      }, ValidationError);
    });

    it('should throw ValidationError for weak password', () => {
      const invalidData = {
        name: 'John Doe',
        email: 'john@example.com',
        password: '123456' // Too weak
      };

      assert.throws(() => {
        UserController.validateCreateUserInput(invalidData);
      }, ValidationError);
    });

    it('should provide detailed error information', () => {
      const invalidData = {
        name: '',
        email: 'invalid-email',
        password: '123'
      };

      try {
        UserController.validateCreateUserInput(invalidData);
        assert.fail('Should have thrown ValidationError');
      } catch (error) {
        assert(error instanceof ValidationError);
        assert.ok(error.details);
        assert.ok(Array.isArray(error.details));
        assert(error.details.length > 0);
        assert.ok(error.details.every(detail => 
          detail.field && detail.message
        ));
      }
    });
  });

  describe('Email Validation', () => {
    it('should validate correct email formats', () => {
      const validEmails = [
        'test@example.com',
        'user.name@domain.co.uk',
        'admin+tag@company.org'
      ];

      validEmails.forEach(email => {
        assert.strictEqual(
          UserController.isValidEmail(email),
          true,
          `Should validate ${email}`
        );
      });
    });

    it('should reject invalid email formats', () => {
      const invalidEmails = [
        'invalid-email',
        '@example.com',
        'test@',
        'test..test@example.com',
        'test@.com',
        'a'.repeat(250) + '@example.com' // Too long
      ];

      invalidEmails.forEach(email => {
        assert.strictEqual(
          UserController.isValidEmail(email),
          false,
          `Should reject ${email}`
        );
      });
    });
  });

  describe('Password Validation', () => {
    it('should validate strong passwords', () => {
      const validPasswords = [
        'SecurePass123!',
        'MyP@ssw0rd',
        'C0mpl3x!P@ss'
      ];

      validPasswords.forEach(password => {
        assert.strictEqual(
          UserController.isValidPassword(password),
          true,
          `Should validate ${password}`
        );
      });
    });

    it('should reject weak passwords', () => {
      const invalidPasswords = [
        '123456',           // Too short, no complexity
        'password',         // No numbers, no special chars
        'PASSWORD123',      // No lowercase
        'password123',      // No uppercase, no special chars
        'Password!',        // No numbers
        'a'.repeat(130)     // Too long
      ];

      invalidPasswords.forEach(password => {
        assert.strictEqual(
          UserController.isValidPassword(password),
          false,
          `Should reject ${password}`
        );
      });
    });
  });
});
```

## Best Practices

### ✅ Validation Best Practices

1. **Validate Early**: Validate inputs at the earliest possible point
2. **Multiple Layers**: Implement validation at controller, service, and database levels
3. **Clear Messages**: Provide specific, actionable error messages
4. **Security First**: Always validate for security threats (XSS, injection, etc.)
5. **Sanitize Input**: Clean and normalize input data
6. **Type Checking**: Ensure data types match expectations
7. **Business Rules**: Enforce domain-specific validation rules
8. **Test Coverage**: Write comprehensive tests for all validation scenarios

### ❌ Validation Anti-Patterns

1. **Client-Side Only**
   ```javascript
   // Wrong - relying only on client-side validation
   // Server must always validate inputs
   ```

2. **Generic Error Messages**
   ```javascript
   // Wrong - unhelpful error messages
   throw new Error('Invalid input');
   
   // Better - specific error messages
   throw new ValidationError('Email must be valid format', 'email');
   ```

3. **Missing Security Validation**
   ```javascript
   // Wrong - not checking for malicious input
   const user = await User.create(req.body);
   
   // Better - validate and sanitize first
   validateInput(req.body);
   const sanitizedData = sanitizeInput(req.body);
   const user = await User.create(sanitizedData);
   ```

4. **Inconsistent Validation**
   ```javascript
   // Wrong - different validation rules in different places
   // Use consistent validation patterns across the application
   ```

Remember: Input validation is your first line of defense against malicious attacks and data corruption. Always validate, sanitize, and verify all user inputs in the WAIF framework.