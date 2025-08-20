# Animation Classes Guide

This guide covers all the smooth animations and transitions implemented throughout the application.

## 🎨 Global Animation Classes

### Base Transitions
- `.smooth-transition` - Standard 0.3s transition with easing
- `.smooth-transition-fast` - Quick 0.2s transition
- `.smooth-transition-slow` - Slow 0.5s transition

### Entry/Exit Animations
- `.fade-in-up` - Fade in with upward movement (matches TransactionModal)
- `.fade-out-down` - Fade out with downward movement

### Loading States
- `.pulse-subtle` - Gentle opacity pulse for loading
- `.pulse-glow` - Glowing pulse effect with box-shadow
- `.skeleton-dark` - Shimmer loading skeleton for dark themes
- `.skeleton-text` - Text skeleton placeholder
- `.skeleton-circle` - Circular skeleton (for avatars)

### Hover Effects

#### Scale Effects
- `.hover-scale-sm` - Small scale on hover (1.02x)
- `.hover-scale-md` - Medium scale on hover (1.05x)

#### Lift Effects
- `.hover-lift` - Subtle lift with shadow (2px up)
- `.hover-lift-lg` - Large lift with shadow (4px up)

#### Glow Effects
- `.hover-glow` - Purple glow on hover
- `.hover-glow-mint` - Mint glow on hover

### Collapsible Sections
- `.accordion-enter-active` / `.accordion-leave-active` - Smooth accordion animations
- `.slide-down-enter-active` - Content slides down when appearing
- `.slide-up-leave-active` - Content slides up when hiding

### List Animations
- `.stagger-item` - Staggered fadeInUp for list items (auto-delays)

## 🔘 Button Enhancements

All button classes now include smooth transitions and hover effects:

### Enhanced Button Variants
- `.btn` - Standard button with lift and glow on hover
- `.btn-outline` - Outlined button with smooth fill transition
- `.btn-ghost` - Transparent button with subtle hover effects
- `.btn-sm` - Small button with proportional animations
- `.btn-lg` - Large button with enhanced hover effects

### Usage Examples
```html
<!-- Standard button with animations -->
<button class="btn hover-lift">Click me</button>

<!-- Outlined button with glow effect -->
<button class="btn-outline hover-glow">Outline Button</button>

<!-- Ghost button for subtle actions -->
<button class="btn-ghost">Ghost Button</button>
```

## 📝 Input Field Enhancements

### Input Classes
- `.input` - Standard input with smooth focus transitions
- `.input-lg` - Large input with enhanced focus ring
- All inputs now have hover states that preview focus colors

### Usage Examples
```html
<!-- Standard input with transitions -->
<input class="input" placeholder="Enter text..." />

<!-- Large input for important fields -->
<input class="input-lg" placeholder="Important field..." />
```

## 🔗 Link Styles

### Link Variants
- `.link` - Simple color transition on hover
- `.link-underline` - Animated underline effect
- `.link-glow` - Text glow effect on hover

### Usage Examples
```html
<!-- Simple link with color transition -->
<a href="#" class="link">Simple Link</a>

<!-- Link with animated underline -->
<a href="#" class="link-underline">Underlined Link</a>

<!-- Link with glow effect -->
<a href="#" class="link-glow">Glowing Link</a>
```

## 🃏 Card Enhancements

### Card Classes
- `.card` - Standard card with hover lift
- `.card-interactive` - Enhanced interactive card with larger hover effects

### Usage Examples
```html
<!-- Standard card with hover effects -->
<div class="card">
  <p>Card content</p>
</div>

<!-- Interactive card for clickable content -->
<div class="card-interactive" @click="handleClick">
  <p>Clickable card content</p>
</div>
```

## 📊 Table Row Animations

Tables now include smooth hover transitions:
- Row hover with slide and shadow effects
- Column header hover states
- Smooth color transitions throughout

## 🎯 Modal Animations

Modal components automatically use the enhanced fadeInUp/fadeOutDown animations from TransactionModal pattern.

## 🔄 Vue Transition Names

### Available Transition Names
- `modal-fade-slide` - For modal components
- `accordion` - For collapsible content
- `slide-down` - For dropdown content
- `slide-up` - For popup content

### Usage in Vue Components
```vue
<template>
  <!-- Modal with animations -->
  <transition name="modal-fade-slide">
    <div v-if="showModal" class="modal">
      Modal content
    </div>
  </transition>

  <!-- Collapsible section -->
  <transition name="accordion">
    <div v-if="isExpanded" class="content">
      Collapsible content
    </div>
  </transition>
</template>
```

## 🎨 Stagger Animations for Lists

For lists that should animate in sequence:

```vue
<template>
  <ul>
    <li v-for="(item, index) in items" :key="item.id" class="stagger-item">
      {{ item.name }}
    </li>
  </ul>
</template>
```

## 💡 Best Practices

1. **Performance**: All animations use `cubic-bezier(0.4, 0, 0.2, 1)` for smooth, performant transitions
2. **Accessibility**: Animations respect user preferences for reduced motion
3. **Consistency**: Use the provided classes for consistent animation timing across the app
4. **Loading States**: Use pulse and skeleton classes for better perceived performance
5. **Interactive Feedback**: Apply hover effects to clickable elements for better UX

## 🔧 Customization

The animations use CSS custom properties where possible, making them themeable:
- `--neon-purple` - Primary accent color
- `--neon-mint` - Secondary accent color
- `--color-bg-dark` - Dark background
- `--color-bg-secondary` - Secondary background

All timing and easing can be customized by modifying the CSS custom properties in your theme files.
