import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { AppComponent } from './app.component';

describe('AppComponent', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AppComponent],
      providers: [provideRouter([])],
    }).compileComponents();
  });

  it('should create the app', () => {
    const fixture = TestBed.createComponent(AppComponent);
    expect(fixture.componentInstance).toBeTruthy();
  });

  it('hides the header on headerless routes when unauthenticated', () => {
    const fixture = TestBed.createComponent(AppComponent);
    // No token in sessionStorage → not authenticated → header hidden
    expect(fixture.componentInstance.showHeader).toBeFalse();
  });
});
