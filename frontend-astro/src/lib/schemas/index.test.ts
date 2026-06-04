import {describe, expect, it} from 'vitest';
import {
  articleSchema,
  changePasswordSchema,
  commentFormSchema,
  commentSchema,
  loginSchema,
  registerSchema,
  searchSchema,
  subscribeSchema,
  twoFactorSchema,
  userProfileSchema,
} from './index';

// ─── loginSchema ───
describe('loginSchema', () => {
  it('should accept valid login data', () => {
    const result = loginSchema.safeParse({username: 'admin', password: '123456'});
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.remember).toBe(false); // default
    }
  });

  it('should accept login with remember=true', () => {
    const result = loginSchema.safeParse({username: 'admin', password: '123456', remember: true});
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.remember).toBe(true);
    }
  });

  it('should reject empty username', () => {
    const result = loginSchema.safeParse({username: '', password: '123456'});
    expect(result.success).toBe(false);
  });

  it('should reject empty password', () => {
    const result = loginSchema.safeParse({username: 'admin', password: ''});
    expect(result.success).toBe(false);
  });

  it('should reject username over 50 chars', () => {
    const result = loginSchema.safeParse({username: 'a'.repeat(51), password: '123456'});
    expect(result.success).toBe(false);
  });

  it('should reject password over 128 chars', () => {
    const result = loginSchema.safeParse({username: 'admin', password: 'a'.repeat(129)});
    expect(result.success).toBe(false);
  });
});

// ─── twoFactorSchema ───
describe('twoFactorSchema', () => {
  it('should accept valid 6-digit TOTP code', () => {
    const result = twoFactorSchema.safeParse({code: '123456'});
    expect(result.success).toBe(true);
  });

  it('should accept valid 8-digit backup code', () => {
    const result = twoFactorSchema.safeParse({code: '12345678'});
    expect(result.success).toBe(true);
  });

  it('should reject code that is not 6 or 8 digits', () => {
    expect(twoFactorSchema.safeParse({code: '12345'}).success).toBe(false);
    expect(twoFactorSchema.safeParse({code: '1234567'}).success).toBe(false);
    expect(twoFactorSchema.safeParse({code: '123456789'}).success).toBe(false);
  });

  it('should reject non-numeric code', () => {
    expect(twoFactorSchema.safeParse({code: 'abcdef'}).success).toBe(false);
  });
});

// ─── registerSchema ───
describe('registerSchema', () => {
  const validData = {
    username: 'testuser',
    email: 'test@example.com',
    password: 'Passw0rd',
    confirmPassword: 'Passw0rd',
    terms: true,
  };

  it('should accept valid registration data', () => {
    const result = registerSchema.safeParse(validData);
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.locale).toBe('zh_CN'); // default
    }
  });

  it('should accept Chinese username', () => {
    const result = registerSchema.safeParse({...validData, username: '测试用户'});
    expect(result.success).toBe(true);
  });

  it('should reject username shorter than 3 chars', () => {
    const result = registerSchema.safeParse({...validData, username: 'ab'});
    expect(result.success).toBe(false);
  });

  it('should reject invalid email', () => {
    const result = registerSchema.safeParse({...validData, email: 'not-an-email'});
    expect(result.success).toBe(false);
  });

  it('should reject password without letters', () => {
    const result = registerSchema.safeParse({...validData, password: '12345678', confirmPassword: '12345678'});
    expect(result.success).toBe(false);
  });

  it('should reject password without digits', () => {
    const result = registerSchema.safeParse({...validData, password: 'abcdefgh', confirmPassword: 'abcdefgh'});
    expect(result.success).toBe(false);
  });

  it('should reject mismatched passwords', () => {
    const result = registerSchema.safeParse({...validData, confirmPassword: 'Different1'});
    expect(result.success).toBe(false);
  });

  it('should reject when terms is not true', () => {
    const result = registerSchema.safeParse({...validData, terms: false});
    expect(result.success).toBe(false);
  });

  it('should reject invalid username characters', () => {
    const result = registerSchema.safeParse({...validData, username: 'user@name!'});
    expect(result.success).toBe(false);
  });
});

// ─── articleSchema ───
describe('articleSchema', () => {
  it('should accept valid article data', () => {
    const result = articleSchema.safeParse({title: 'Test Article'});
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.status).toBe(0); // default
      expect(result.data.hidden).toBe(false); // default
    }
  });

  it('should reject empty title', () => {
    const result = articleSchema.safeParse({title: ''});
    expect(result.success).toBe(false);
  });

  it('should accept article with all optional fields', () => {
    const result = articleSchema.safeParse({
      title: 'Test',
      slug: 'test-slug',
      excerpt: 'An excerpt',
      cover_image: 'https://example.com/img.jpg',
      category_id: 1,
      tags: 'tag1,tag2',
      status: 1,
      hidden: true,
      is_vip_only: true,
    });
    expect(result.success).toBe(true);
  });

  it('should coerce category_id string to number', () => {
    const result = articleSchema.safeParse({title: 'Test', category_id: '5'});
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.category_id).toBe(5);
    }
  });
});

// ─── commentSchema ───
describe('commentSchema', () => {
  it('should accept valid comment', () => {
    const result = commentSchema.safeParse({content: 'Hello world!'});
    expect(result.success).toBe(true);
  });

  it('should accept comment with parent_id', () => {
    const result = commentSchema.safeParse({content: 'Reply', parent_id: 5});
    expect(result.success).toBe(true);
  });

  it('should reject empty content', () => {
    const result = commentSchema.safeParse({content: ''});
    expect(result.success).toBe(false);
  });

  it('should reject content over 2000 chars', () => {
    const result = commentSchema.safeParse({content: 'a'.repeat(2001)});
    expect(result.success).toBe(false);
  });
});

// ─── commentFormSchema ───
describe('commentFormSchema', () => {
  it('should accept valid comment form with optional author', () => {
    const result = commentFormSchema.safeParse({
      content: 'Nice article!',
      author_name: 'John',
      author_email: 'john@example.com',
    });
    expect(result.success).toBe(true);
  });

  it('should accept empty author_email', () => {
    const result = commentFormSchema.safeParse({content: 'Nice!', author_email: ''});
    expect(result.success).toBe(true);
  });

  it('should reject invalid author_email', () => {
    const result = commentFormSchema.safeParse({content: 'Nice!', author_email: 'bad'});
    expect(result.success).toBe(false);
  });
});

// ─── userProfileSchema ───
describe('userProfileSchema', () => {
  it('should accept valid profile data', () => {
    const result = userProfileSchema.safeParse({email: 'user@test.com'});
    expect(result.success).toBe(true);
  });

  it('should accept full profile', () => {
    const result = userProfileSchema.safeParse({
      nickname: 'Nick',
      email: 'user@test.com',
      bio: 'A bio',
      avatar: 'https://example.com/avatar.png',
    });
    expect(result.success).toBe(true);
  });

  it('should reject invalid email', () => {
    const result = userProfileSchema.safeParse({email: 'invalid'});
    expect(result.success).toBe(false);
  });
});

// ─── changePasswordSchema ───
describe('changePasswordSchema', () => {
  const validData = {
    current_password: 'OldPass1',
    new_password: 'NewPass123',
    confirm_password: 'NewPass123',
  };

  it('should accept valid password change', () => {
    const result = changePasswordSchema.safeParse(validData);
    expect(result.success).toBe(true);
  });

  it('should reject mismatched new passwords', () => {
    const result = changePasswordSchema.safeParse({...validData, confirm_password: 'Different1'});
    expect(result.success).toBe(false);
  });

  it('should reject weak new password', () => {
    const result = changePasswordSchema.safeParse({
      ...validData,
      new_password: '12345678',
      confirm_password: '12345678'
    });
    expect(result.success).toBe(false);
  });
});

// ─── searchSchema ───
describe('searchSchema', () => {
  it('should accept valid search query', () => {
    const result = searchSchema.safeParse({query: 'hello'});
    expect(result.success).toBe(true);
  });

  it('should reject empty query', () => {
    const result = searchSchema.safeParse({query: ''});
    expect(result.success).toBe(false);
  });

  it('should reject query over 200 chars', () => {
    const result = searchSchema.safeParse({query: 'a'.repeat(201)});
    expect(result.success).toBe(false);
  });
});

// ─── subscribeSchema ───
describe('subscribeSchema', () => {
  it('should accept valid email', () => {
    const result = subscribeSchema.safeParse({email: 'user@example.com'});
    expect(result.success).toBe(true);
  });

  it('should reject invalid email', () => {
    const result = subscribeSchema.safeParse({email: 'not-valid'});
    expect(result.success).toBe(false);
  });
});
