export class Statistics {

    /**
     * Calculate the arithmetic mean (average) of an array of numbers
     * @param numbers - Array of numbers to calculate the mean of
     * @returns The arithmetic mean value
     */
    static mean(numbers: number[]) {
        // Calculate sum and divide by the count of numbers
        const sum = numbers.reduce((accumulator, currentValue) => accumulator + currentValue, 0);
        const mean = sum / numbers.length;

        return mean
    }

    /**
     * Calculate the median (middle value) of an array of numbers
     * @param numbers - Array of numbers to calculate the median of
     * @returns The median value
     */
    static median(numbers: number[]) {
        //Sort numbers
        numbers.sort()

        //Find the median index
        const medianIndex = numbers.length / 2

        let medianValue: number;
        if (numbers.length % 2 !== 0) {
            //If number is odd
            medianValue = numbers[Math.floor(medianIndex)]
        } else {
            //If number is even
            medianValue = (numbers[medianIndex] + numbers[medianIndex - 1]) / 2
        }
    }

    /**
     * Calculate the mode (most frequent value(s)) of an array of numbers
     * @param numbers - Array of numbers to calculate the mode of
     * @returns Object containing the mode value(s) and their frequency
     */
    static mode(numbers: number[]) {
        const modeMap = new Map<number, number>()

        //Set each entry parameter into the map and assign it the number of times it appears in the list
        numbers.forEach((value) => {
            if (modeMap.has(value)) {
                modeMap.set(value, modeMap.get(value)! + 1)
            } else {
                modeMap.set(value, 1)
            }
        });

        //Find the max frequency in the map
        let maxFrequency = 0;
        for (const numberFrequency of modeMap.values()) {
            if (numberFrequency > maxFrequency) {
                maxFrequency = numberFrequency;
            }
        }

        const modeResult = []
        //Find the entries with the highest frequency
        for (const [key, value] of modeMap.entries()) {
            if (value === maxFrequency) {
                modeResult.push(key)
            }
        }

        return {
            modeResult: modeResult,
            maxFrequency: maxFrequency
        }
    }

    /**
     * Find the minimum value in an array of numbers
     * @param numbers - Array of numbers to find the minimum of
     * @returns The minimum value
     */
    static min(numbers: number[]) {
        const minValue = Math.min(...numbers);

        return minValue
    }

    /**
     * Find the maximum value in an array of numbers
     * @param numbers - Array of numbers to find the maximum of
     * @returns The maximum value
     */
    static max(numbers: number[]) {
        const maxValue = Math.max(...numbers);

        return maxValue
    }

}
