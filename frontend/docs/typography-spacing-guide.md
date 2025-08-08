# Typography & Spacing System Guide

## Overview
This guide documents the consistent typography hierarchy and spacing system established for the pyNance application. The system ensures visual consistency, proper vertical rhythm, and improved readability across all components.

## Typography Hierarchy

### Heading Scales

#### H1 - Main Page Headers (2.5rem / 40px)
```css
/* Usage */
.h1 { font-size: var(--font-size-5xl); font-weight: var(--font-weight-bold); }

/* HTML Examples */
<h1>Dashboard Overview</h1>
<div class="h1">Portfolio Summary</div>
```

#### H2 - Section Headers (2rem / 32px)
```css
.h2 { font-size: var(--font-size-4xl); font-weight: var(--font-weight-bold); }

<!-- HTML Examples -->
<h2>Recent Transactions</h2>
<div class="h2">Account Balance</div>
```

#### H3 - Subsection Headers (1.5rem / 24px)
```css
.h3 { font-size: var(--font-size-2xl); font-weight: var(--font-weight-semibold); }

<!-- HTML Examples -->
<h3>Investment Categories</h3>
<div class="h3">Monthly Summary</div>
```

### Body Text

#### Primary Body Text (1rem / 16px)
```css
body, .body-text { 
  font-size: var(--font-size-base); 
  line-height: var(--line-height-normal); 
}

<!-- Standard paragraph text -->
<p>This is regular body text with optimal line height for readability.</p>
```

#### Small Text - Labels & Captions (0.875rem / 14px)
```css
.text-small, .label, .caption { font-size: var(--font-size-sm); }

<!-- Form labels -->
<label class="label">Account Name</label>

<!-- Descriptive text -->
<span class="caption">Last updated 2 hours ago</span>
```

### Font Weights

- **Normal (400)**: Standard body text
- **Semibold (600)**: Subheadings, labels, emphasized text
- **Bold (800)**: Main headings, important callouts

```css
.font-normal { font-weight: var(--font-weight-normal); }
.font-semibold { font-weight: var(--font-weight-semibold); }
.font-bold { font-weight: var(--font-weight-bold); }
```

## Spacing System

### Spacing Scale
Our spacing system uses a consistent scale based on multiples of 4px:

```css
--space-1: 0.25rem;   /* 4px */
--space-2: 0.5rem;    /* 8px */
--space-4: 1rem;      /* 16px */
--space-6: 1.5rem;    /* 24px */
--space-8: 2rem;      /* 32px */
--space-12: 3rem;     /* 48px */
```

### Margin Utilities

```css
/* All sides */
.m-1, .m-2, .m-4, .m-6, .m-8, .m-12

/* Specific sides */
.mt-4  /* margin-top */
.mb-6  /* margin-bottom */
.ml-2  /* margin-left */
.mr-8  /* margin-right */

/* Examples */
<div class="mb-8">Section with bottom margin</div>
<h2 class="mt-12 mb-6">Spaced heading</h2>
```

### Padding Utilities

```css
/* All sides */
.p-1, .p-2, .p-4, .p-6, .p-8, .p-12

/* Specific sides */
.pt-4  /* padding-top */
.pb-6  /* padding-bottom */
.pl-2  /* padding-left */
.pr-8  /* padding-right */

/* Examples */
<div class="p-6">Evenly padded content</div>
<section class="pt-12 pb-8">Vertical padding</section>
```

### Gap Utilities (Flexbox/Grid)

```css
.gap-1, .gap-2, .gap-4, .gap-6, .gap-8, .gap-12

/* Examples */
<div class="flex gap-4">Flexbox with 16px gap</div>
<div class="grid grid-cols-3 gap-6">Grid with 24px gap</div>
```

## Container & Section Classes

### Container Padding Variants

```css
.container-sm { padding: var(--container-padding-sm); }   /* 16px */
.container-md { padding: var(--container-padding-md); }   /* 24px */
.container-lg { padding: var(--container-padding-lg); }   /* 32px */

/* Examples */
<div class="card container-md">Medium padded card</div>
<section class="container-lg">Large padded section</section>
```

### Section Spacing for Vertical Rhythm

```css
.section    { margin-bottom: var(--section-spacing-md); }   /* 48px */
.section-sm { margin-bottom: var(--section-spacing-sm); }   /* 32px */
.section-lg { margin-bottom: var(--section-spacing-lg); }   /* 64px */

/* Examples */
<section class="section">
  <h2>Portfolio Overview</h2>
  <p>Content with proper bottom spacing</p>
</section>
```

### Enhanced Card Classes

The existing card classes now use consistent padding from the spacing system:

```css
.card {
  padding: var(--container-padding-md);      /* 24px */
  margin-bottom: var(--section-spacing-sm);  /* 32px */
}

.card-content     { padding: var(--container-padding-md); }   /* 24px */
.card-content-sm  { padding: var(--container-padding-sm); }   /* 16px */
.card-content-lg  { padding: var(--container-padding-lg); }   /* 32px */
```

## Responsive Behavior

### Mobile Breakpoints

**Tablet (768px and below):**
- H1 reduces to 2rem (from 2.5rem)
- H2 reduces to 1.875rem (from 2rem)
- H3 reduces to 1.25rem (from 1.5rem)
- Section spacing reduces proportionally

**Mobile (480px and below):**
- H1 reduces to 1.875rem
- H2 reduces to 1.5rem
- Container padding reduces to maintain readability

## Implementation Examples

### Dashboard Card with Proper Typography

```html
<div class="card">
  <h3 class="mb-4">Account Summary</h3>
  <div class="mb-6">
    <label class="label">Total Balance</label>
    <p class="font-semibold text-2xl">$12,453.67</p>
  </div>
  <div class="flex gap-4">
    <button class="btn">View Details</button>
    <button class="btn-outline">Export</button>
  </div>
</div>
```

### Form with Consistent Spacing

```html
<form class="section">
  <h2 class="mb-8">Add New Transaction</h2>
  
  <div class="mb-6">
    <label class="label">Transaction Type</label>
    <select class="input mt-1">
      <option>Income</option>
      <option>Expense</option>
    </select>
  </div>
  
  <div class="mb-6">
    <label class="label">Amount</label>
    <input type="number" class="input mt-1" placeholder="0.00">
    <span class="caption mt-1">Enter amount in USD</span>
  </div>
  
  <div class="flex gap-4 mt-8">
    <button type="submit" class="btn">Save Transaction</button>
    <button type="button" class="btn-ghost">Cancel</button>
  </div>
</form>
```

## CSS Variables Reference

### Typography Variables
```css
/* Font Sizes */
--font-size-sm: 0.875rem;
--font-size-base: 1rem;
--font-size-lg: 1.125rem;
--font-size-xl: 1.25rem;
--font-size-2xl: 1.5rem;
--font-size-3xl: 1.875rem;
--font-size-4xl: 2rem;
--font-size-5xl: 2.5rem;

/* Font Weights */
--font-weight-normal: 400;
--font-weight-semibold: 600;
--font-weight-bold: 800;

/* Line Heights */
--line-height-tight: 1.2;
--line-height-normal: 1.6;
--line-height-relaxed: 1.8;
```

### Spacing Variables
```css
/* Base Spacing */
--space-1: 0.25rem;
--space-2: 0.5rem;
--space-4: 1rem;
--space-6: 1.5rem;
--space-8: 2rem;
--space-12: 3rem;

/* Container Padding */
--container-padding-sm: var(--space-4);
--container-padding-md: var(--space-6);
--container-padding-lg: var(--space-8);

/* Section Spacing */
--section-spacing-sm: var(--space-8);
--section-spacing-md: var(--space-12);
--section-spacing-lg: 4rem;
```

## Best Practices

1. **Consistency**: Always use the defined scale instead of arbitrary values
2. **Vertical Rhythm**: Maintain consistent spacing between sections
3. **Hierarchy**: Use appropriate heading levels and don't skip levels
4. **Responsive**: Test typography at different screen sizes
5. **Accessibility**: Ensure sufficient color contrast and readable line heights
6. **Performance**: Use CSS classes instead of inline styles

## Migration Guide

When updating existing components:

1. Replace hardcoded font sizes with typography classes
2. Update padding/margin values to use spacing utilities
3. Ensure proper heading hierarchy (h1 → h2 → h3)
4. Add section spacing for better vertical rhythm
5. Test responsive behavior on mobile devices

This system provides a solid foundation for consistent, accessible, and maintainable typography and spacing across the entire application.
