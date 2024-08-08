// 헤더 스크롤
window.addEventListener('scroll', function() {
    const header = document.getElementById('head');
    if (window.scrollY > 10) { // Adjust the scroll threshold as needed
        header.classList.add('scrolled');
    } else {
        header.classList.remove('scrolled');
    }
});


document.addEventListener('DOMContentLoaded', (event) => {

// 헤더 스크롤(새로고침)
const header = document.getElementById('head');
if (window.scrollY > 10) {
    header.classList.add('scrolled');
}

//다이어리 슬라이드
function initializeSlider() {

    const sliderContainer = document.querySelector('.slider-container');
    if (!sliderContainer) return; // sliderContainer가 존재하지 않으면 스크립트 종료

    const slider = sliderContainer.querySelector('.slider');
    const nextButton = sliderContainer.querySelector('#next');
    const prevButton = sliderContainer.querySelector('#prev');
    const slide = sliderContainer.querySelector('.card');
    const cards = sliderContainer.querySelectorAll('.card');
    let currentIndex = 0;
    let accumulatedDistance = 0;

    function getSlideDetails() {
        const slideWidth = slide ? slide.offsetWidth : 0; // 카드가 없을 경우를 대비하여 0으로 설정
        const marginLeft = slide ? parseFloat(getComputedStyle(slide).marginLeft) : 0; // 카드가 없을 경우를 대비하여 0으로 설정
        return { slideWidth, marginLeft };
    }

    function updateSliderPosition() {
        const { slideWidth, marginLeft } = getSlideDetails();
        if (currentIndex === 0) {
            accumulatedDistance = 0;
        } else {
            accumulatedDistance = -((slideWidth + marginLeft) * (currentIndex - 1) + (slideWidth / 2 + marginLeft));
        }
        slider.style.transform = `translateX(${accumulatedDistance}px)`;
    }

    function updateSliderButtons() {
        const sliderContainerWidth = sliderContainer.offsetWidth;
        const sliderWidth = slider.offsetWidth;

        if (cards.length === 0 || sliderWidth <= sliderContainerWidth) {
            nextButton.style.display = 'none';
            prevButton.style.display = 'none';
            currentIndex = 0;
            updateSliderPosition();
        } else {
            nextButton.style.display = currentIndex === cards.length - 1 ? 'none' : 'flex';
            prevButton.style.display = currentIndex === 0 ? 'none' : 'flex';
        }
    }

    nextButton.addEventListener('click', () => {
        const { slideWidth, marginLeft } = getSlideDetails();
        let moveDistance;
        if (currentIndex === 0) {
            moveDistance = (slideWidth / 2) + marginLeft;
        } else {
            moveDistance = slideWidth + marginLeft;
        }
        accumulatedDistance -= moveDistance;
        currentIndex++;
        slider.style.transform = `translateX(${accumulatedDistance}px)`;
        updateSliderButtons();
    });

    prevButton.addEventListener('click', () => {
        if (currentIndex === 0) return;
        const { slideWidth, marginLeft } = getSlideDetails();
        let moveDistance;
        if (currentIndex === 1) {
            moveDistance = (slideWidth / 2) + marginLeft;
        } else {
            moveDistance = slideWidth + marginLeft;
        }
        accumulatedDistance += moveDistance;
        currentIndex--;
        slider.style.transform = `translateX(${accumulatedDistance}px)`;
        updateSliderButtons();
    });

    // 초기 상태 버튼 업데이트
    updateSliderButtons();

    // 창 크기 변경 이벤트 리스너 추가
    window.addEventListener('resize', () => {
        updateSliderPosition();
        updateSliderButtons();
    });


    // card 넓이
    function adjustCardWidth() {
        const containerWidth = sliderContainer.offsetWidth; // .slider-container의 너비 가져오기

        let cardWidth;

        // 화면 너비가 768px 이하인 경우
        if (window.innerWidth < 720) {
            cardWidth = `calc((${containerWidth}px * 0.66) - 1.5rem)`; // .66으로 계산
            cards.forEach(card => {
                card.style.maxWidth = 'none';
            });
        } else {
            cardWidth = `calc((${containerWidth}px * 0.4) - 1.5rem)`; // 기본값인 .4로 계산
            cards.forEach(card => {
                card.style.maxWidth = '300px';
            });
        }
        // 각 카드에 너비 설정
        cards.forEach(card => {
            card.style.width = cardWidth;
        });
        updateSliderButtons();
    }

    // 페이지 로드 시 및 리사이즈 이벤트 시 호출
    window.addEventListener('load', adjustCardWidth);
    window.addEventListener('resize', adjustCardWidth);

    // 카드가 없는 경우 버튼 숨기기
    updateSliderButtons();

}
initializeSlider();



// 슬라이드
function setupslideTour() {
    const slideTour = document.querySelector('.slide_tour');
    if (!slideTour) return;

    const slider = slideTour.querySelector('.slider');
    const nextButton = slideTour.querySelector('#next');
    const prevButton = slideTour.querySelector('#prev');
    const slides = slider.querySelectorAll('.slider li');
    let currentIndex = 0;

    // 슬라이드의 너비 가져오기
    const slideWidth = slides.length > 0 ? slides[0].offsetWidth : 0;

    // 다음 버튼 클릭 시
    nextButton.addEventListener('click', () => {
        if (currentIndex < slides.length - 1) {
            currentIndex++;
            updateSlider(slider, currentIndex);
            updateSliderButtons();
        }
    });

    // 이전 버튼 클릭 시
    prevButton.addEventListener('click', () => {
        if (currentIndex > 0) {
            currentIndex--;
            updateSlider(slider, currentIndex);
            updateSliderButtons();

        }
    });

    // 슬라이더 위치 업데이트
    function updateSlider(slider, currentIndex) {
        const offset = -currentIndex * slideWidth;
        slider.style.transform = `translateX(${offset}px)`;
    }

    function updateSliderButtons() {
        const slideTourWidth = slideTour.offsetWidth;
        const sliderWidth = slider.offsetWidth;

        if (slides.length === 0 || sliderWidth <= slideTourWidth) {
            nextButton.style.display = 'none';
            prevButton.style.display = 'none';
            currentIndex = 0;
            updateSlider(slider, currentIndex);
        } else {
            nextButton.style.display = currentIndex === slides.length - 1 ? 'none' : 'flex';
            prevButton.style.display = currentIndex === 0 ? 'none' : 'flex';
        }
    }

    // 터치 이벤트 추가
    let startX = 0;
    let endX = 0;

    // 터치 시작
    slider.addEventListener('touchstart', (event) => {
        startX = event.touches[0].clientX;
        document.body.style.overflow = 'hidden'; // 스크롤 방지

    });

    // 터치 끝
    slider.addEventListener('touchend', (event) => {
        endX = event.changedTouches[0].clientX;
        handleSwipe();
        document.body.style.overflow = ''; // 스크롤 다시 활성화

    });

    // 스와이프 처리
    function handleSwipe() {
        if (startX > endX + 50) {
            if (currentIndex < slides.length - 1) {
                currentIndex++;
                updateSlider(slider, currentIndex);
                updateSliderButtons();
            }
        } else if (startX < endX - 50) {
            if (currentIndex > 0) {
                currentIndex--;
                updateSlider(slider, currentIndex);
                updateSliderButtons();
            }
        }
    }

    // 초기 슬라이더 업데이트
    updateSlider(slider, currentIndex);
    updateSliderButtons();

    // 창 크기 변경 이벤트 리스너 추가
    window.addEventListener('resize', () => {
        updateSliderButtons();
    });


}
setupslideTour();



});