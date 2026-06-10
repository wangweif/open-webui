if (!Array.prototype.at) {
	Object.defineProperty(Array.prototype, 'at', {
		value(this: ArrayLike<unknown>, index: number) {
			const length = this.length;
			const relativeIndex = Math.trunc(Number(index)) || 0;
			const actualIndex = relativeIndex >= 0 ? relativeIndex : length + relativeIndex;

			if (actualIndex < 0 || actualIndex >= length) {
				return undefined;
			}

			return this[actualIndex];
		},
		writable: true,
		enumerable: false,
		configurable: true
	});
}

if (!String.prototype.at) {
	Object.defineProperty(String.prototype, 'at', {
		value(this: string, index: number) {
			const value = String(this);
			const length = value.length;
			const relativeIndex = Math.trunc(Number(index)) || 0;
			const actualIndex = relativeIndex >= 0 ? relativeIndex : length + relativeIndex;

			if (actualIndex < 0 || actualIndex >= length) {
				return undefined;
			}

			return value.charAt(actualIndex);
		},
		writable: true,
		enumerable: false,
		configurable: true
	});
}

if (typeof crypto !== 'undefined' && !crypto.randomUUID && crypto.getRandomValues) {
	Object.defineProperty(crypto, 'randomUUID', {
		value() {
			return '10000000-1000-4000-8000-100000000000'.replace(/[018]/g, (character) => {
				const value =
					Number(character) ^
					(crypto.getRandomValues(new Uint8Array(1))[0] & (15 >> (Number(character) / 4)));

				return value.toString(16);
			});
		},
		writable: true,
		configurable: true
	});
}
